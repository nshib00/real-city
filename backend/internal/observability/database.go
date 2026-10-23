package observability

import (
	"context"
	"database/sql"
	"errors"
	"sort"
	"strconv"
	"sync"
	"sync/atomic"
	"time"

	"github.com/lib/pq"

	"real-city/backend/pkg/apperror"
)

// DBBuckets are seconds. Operation names are fixed at call sites, never SQL or IDs.
var DBBuckets = [...]float64{0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5}

type durationSample struct {
	count   uint64
	sum     float64
	buckets [len(DBBuckets)]uint64
}

var durations = struct {
	sync.Mutex
	db        map[string]*durationSample
	world     map[string]*durationSample
	placement map[string]*durationSample
}{db: make(map[string]*durationSample), world: make(map[string]*durationSample), placement: make(map[string]*durationSample)}

var cacheHits atomic.Uint64
var cacheMisses atomic.Uint64
var chunksCreated atomic.Uint64
var cacheEntries atomic.Int64

func Result(err error) string {
	if err == nil {
		return "ok"
	}
	if errors.Is(err, context.DeadlineExceeded) {
		return "timeout"
	}
	if errors.Is(err, sql.ErrNoRows) {
		return "not_found"
	}
	var pgErr *pq.Error
	if errors.As(err, &pgErr) {
		if string(pgErr.Code) == "57014" {
			return "timeout"
		}
		if len(pgErr.Code) >= 2 && string(pgErr.Code[:2]) == "23" {
			return "conflict"
		}
	}
	var appErr *apperror.Error
	if errors.As(err, &appErr) {
		switch appErr.Kind {
		case apperror.NotFound:
			return "not_found"
		case apperror.Conflict:
			return "conflict"
		}
	}
	return "error"
}

func observe(target map[string]*durationSample, key string, elapsed time.Duration) {
	durations.Lock()
	sample := target[key]
	if sample == nil {
		sample = &durationSample{}
		target[key] = sample
	}
	sample.count++
	seconds := elapsed.Seconds()
	sample.sum += seconds
	for i, bound := range DBBuckets {
		if seconds <= bound {
			sample.buckets[i]++
		}
	}
	durations.Unlock()
}

func ObserveDB(operation string, started time.Time, err error) {
	observe(durations.db, operation+"|"+Result(err), time.Since(started))
}

func ObserveWorld(operation string, started time.Time, err error) {
	observe(durations.world, operation+"|"+Result(err), time.Since(started))
}

func ObservePlacement(component string, started time.Time, err error) {
	observe(durations.placement, component+"|"+Result(err), time.Since(started))
}

func CacheLookup(hit bool) {
	if hit {
		cacheHits.Add(1)
	} else {
		cacheMisses.Add(1)
	}
}

func ChunkCreated()         { chunksCreated.Add(1) }
func SetCacheEntries(n int) { cacheEntries.Store(int64(n)) }

func WriteDB(w Writer, pool *sql.DB) {
	w.Family("real_city_db_pool_open_connections", "Open database connections.", "gauge")
	w.Family("real_city_db_pool_in_use_connections", "Database connections in use.", "gauge")
	w.Family("real_city_db_pool_idle_connections", "Idle database connections.", "gauge")
	w.Family("real_city_db_pool_max_open_connections", "Configured maximum open connections.", "gauge")
	w.Family("real_city_db_pool_wait_count_total", "Requests that waited for a database connection.", "counter")
	w.Family("real_city_db_pool_wait_duration_seconds_total", "Time spent waiting for database connections.", "counter")
	w.Family("real_city_db_pool_max_idle_closed_total", "Connections closed due to maximum idle limit.", "counter")
	w.Family("real_city_db_pool_max_idle_time_closed_total", "Connections closed due to idle timeout.", "counter")
	w.Family("real_city_db_pool_max_lifetime_closed_total", "Connections closed due to lifetime limit.", "counter")
	if pool != nil {
		s := pool.Stats()
		w.Sample("real_city_db_pool_open_connections", nil, float64(s.OpenConnections))
		w.Sample("real_city_db_pool_in_use_connections", nil, float64(s.InUse))
		w.Sample("real_city_db_pool_idle_connections", nil, float64(s.Idle))
		w.Sample("real_city_db_pool_max_open_connections", nil, float64(s.MaxOpenConnections))
		w.Sample("real_city_db_pool_wait_count_total", nil, float64(s.WaitCount))
		w.Sample("real_city_db_pool_wait_duration_seconds_total", nil, s.WaitDuration.Seconds())
		w.Sample("real_city_db_pool_max_idle_closed_total", nil, float64(s.MaxIdleClosed))
		w.Sample("real_city_db_pool_max_idle_time_closed_total", nil, float64(s.MaxIdleTimeClosed))
		w.Sample("real_city_db_pool_max_lifetime_closed_total", nil, float64(s.MaxLifetimeClosed))
	}
	writeDurations(w, "real_city_db_operation_duration_seconds", "Duration of named Postgres repository operations, including connection wait and row scan.", "operation", durations.db)
	writeDurations(w, "real_city_world_operation_duration_seconds", "Duration of world operations spanning cache, generation and database work.", "operation", durations.world)
	writeDurations(w, "real_city_building_placement_duration_seconds", "Duration of building placement service stages.", "component", durations.placement)
	w.Family("real_city_world_cache_lookups_total", "World chunk cache lookups by result.", "counter")
	w.Sample("real_city_world_cache_lookups_total", map[string]string{"result": "hit"}, float64(cacheHits.Load()))
	w.Sample("real_city_world_cache_lookups_total", map[string]string{"result": "miss"}, float64(cacheMisses.Load()))
	w.Family("real_city_world_cache_entries", "Current world chunk cache entries.", "gauge")
	w.Sample("real_city_world_cache_entries", nil, float64(cacheEntries.Load()))
	w.Family("real_city_world_chunks_created_total", "New world chunks committed to Postgres.", "counter")
	w.Sample("real_city_world_chunks_created_total", nil, float64(chunksCreated.Load()))
}

func writeDurations(w Writer, name, help, label string, source map[string]*durationSample) {
	w.Family(name, help, "histogram")
	durations.Lock()
	copyOf := make(map[string]durationSample, len(source))
	for key, sample := range source {
		copyOf[key] = *sample
	}
	durations.Unlock()
	keys := make([]string, 0, len(copyOf))
	for key := range copyOf {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		s := copyOf[key]
		separator := -1
		for i := range key {
			if key[i] == '|' {
				separator = i
				break
			}
		}
		if separator < 0 {
			continue
		}
		labels := map[string]string{label: key[:separator], "result": key[separator+1:]}
		for i, bound := range DBBuckets {
			labels["le"] = strconv.FormatFloat(bound, 'g', -1, 64)
			w.Sample(name+"_bucket", labels, float64(s.buckets[i]))
		}
		labels["le"] = "+Inf"
		w.Sample(name+"_bucket", labels, float64(s.count))
		delete(labels, "le")
		w.Sample(name+"_sum", labels, s.sum)
		w.Sample(name+"_count", labels, float64(s.count))
	}
}

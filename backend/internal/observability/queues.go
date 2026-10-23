package observability

import (
	"sync"
	"time"
)

type QueueState struct {
	Pending, Due, Dead float64
	OldestDueAge       float64
}

var queueMetrics = struct {
	sync.RWMutex
	values  map[string]QueueState
	updated float64
}{values: map[string]QueueState{}}

// SetQueueSnapshot replaces all samples atomically after a successful collection.
func SetQueueSnapshot(values map[string]QueueState) {
	queueMetrics.Lock()
	queueMetrics.values = values
	queueMetrics.updated = float64(time.Now().UnixNano()) / 1e9
	queueMetrics.Unlock()
}

func WriteQueues(w Writer) {
	queueMetrics.RLock()
	defer queueMetrics.RUnlock()
	w.Family("real_city_queue_pending", "Items waiting in a queue (including future due items).", "gauge")
	w.Family("real_city_queue_due", "Items whose due time has passed, including locked items.", "gauge")
	w.Family("real_city_queue_oldest_due_age_seconds", "Age of oldest due item at last database sample.", "gauge")
	w.Family("real_city_queue_dead", "Dead letter count; only outbox has dead letters.", "gauge")
	for _, name := range []string{"actions", "outbox", "buildings", "production"} {
		v, ok := queueMetrics.values[name]
		if !ok {
			continue
		}
		labels := map[string]string{"component": name}
		w.Sample("real_city_queue_pending", labels, v.Pending)
		w.Sample("real_city_queue_due", labels, v.Due)
		w.Sample("real_city_queue_oldest_due_age_seconds", labels, v.OldestDueAge)
		if name == "outbox" {
			w.Sample("real_city_queue_dead", nil, v.Dead)
		}
	}
	w.Family("real_city_queue_snapshot_timestamp_seconds", "Unix time of last successful database backlog collection.", "gauge")
	if queueMetrics.updated != 0 {
		w.Sample("real_city_queue_snapshot_timestamp_seconds", nil, queueMetrics.updated)
	}
}

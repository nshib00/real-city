package observability

import (
	"fmt"
	"io"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"time"
)

var processStart = time.Now()

// Writer emits Prometheus text format 0.0.4. Call Family before its samples.
type Writer struct{ Out io.Writer }

func (w Writer) Family(name, help, metricType string) {
	fmt.Fprintf(w.Out, "# HELP %s %s\n# TYPE %s %s\n", name, strings.ReplaceAll(help, "\n", " "), name, metricType)
}

func (w Writer) Sample(name string, labels map[string]string, value float64) {
	fmt.Fprint(w.Out, name)
	if len(labels) > 0 {
		// All callers pass a fixed label vocabulary. Sorting makes scrapes stable.
		keys := make([]string, 0, len(labels))
		for key := range labels {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		fmt.Fprint(w.Out, "{")
		for i, key := range keys {
			if i > 0 {
				fmt.Fprint(w.Out, ",")
			}
			value := strings.NewReplacer("\\", "\\\\", "\n", "\\n", "\"", "\\\"").Replace(labels[key])
			fmt.Fprintf(w.Out, "%s=\"%s\"", key, value)
		}
		fmt.Fprint(w.Out, "}")
	}
	fmt.Fprintf(w.Out, " %s\n", strconv.FormatFloat(value, 'g', -1, 64))
}

func WriteRuntime(w Writer) {
	var mem runtime.MemStats
	runtime.ReadMemStats(&mem)
	w.Family("real_city_go_goroutines", "Current number of Go goroutines.", "gauge")
	w.Sample("real_city_go_goroutines", nil, float64(runtime.NumGoroutine()))
	w.Family("real_city_go_heap_alloc_bytes", "Bytes of allocated Go heap objects.", "gauge")
	w.Sample("real_city_go_heap_alloc_bytes", nil, float64(mem.HeapAlloc))
	w.Family("real_city_go_heap_inuse_bytes", "Bytes of Go heap spans in use.", "gauge")
	w.Sample("real_city_go_heap_inuse_bytes", nil, float64(mem.HeapInuse))
	w.Family("real_city_go_gc_cycles_total", "Completed Go garbage collection cycles.", "counter")
	w.Sample("real_city_go_gc_cycles_total", nil, float64(mem.NumGC))
	w.Family("real_city_process_start_time_seconds", "Process start time in Unix seconds.", "gauge")
	w.Sample("real_city_process_start_time_seconds", nil, float64(processStart.UnixNano())/1e9)
}

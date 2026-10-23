package observability

import (
	"bytes"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestWriterEscapesLabels(t *testing.T) {
	var output bytes.Buffer
	w := Writer{Out: &output}
	w.Family("example_total", "one\nline", "counter")
	w.Sample("example_total", map[string]string{"result": "a\\b\"c\nd"}, 1)
	if got, want := output.String(), "# HELP example_total one line\n# TYPE example_total counter\nexample_total{result=\"a\\\\b\\\"c\\nd\"} 1\n"; got != want {
		t.Fatalf("exposition = %q, want %q", got, want)
	}
}

func TestDurationHistogramAndEmptyQueues(t *testing.T) {
	var output bytes.Buffer
	WriteQueues(Writer{Out: &output})
	if !strings.Contains(output.String(), "# TYPE real_city_queue_due gauge") {
		t.Fatal("empty queue snapshot has no family")
	}
	var sample durationSample
	sample.count = 2
	sample.sum = 0.003
	for i := range sample.buckets {
		sample.buckets[i] = 2
	}
	var histogram bytes.Buffer
	writeDurations(Writer{Out: &histogram}, "example_duration_seconds", "test", "operation", map[string]*durationSample{"lookup|ok": &sample})
	for _, want := range []string{
		`example_duration_seconds_bucket{le="+Inf",operation="lookup",result="ok"} 2`,
		`example_duration_seconds_count{operation="lookup",result="ok"} 2`,
		`example_duration_seconds_sum{operation="lookup",result="ok"} 0.003`,
	} {
		if !strings.Contains(histogram.String(), want) {
			t.Errorf("missing histogram sample %q", want)
		}
	}
}

func TestConcurrentDurationSnapshots(t *testing.T) {
	var group sync.WaitGroup
	start := time.Now().Add(-time.Millisecond)
	for range 8 {
		group.Add(1)
		go func() {
			defer group.Done()
			for range 100 {
				ObserveDB("test.concurrent", start, nil)
				var output bytes.Buffer
				WriteDB(Writer{Out: &output}, nil)
			}
		}()
	}
	group.Wait()
}

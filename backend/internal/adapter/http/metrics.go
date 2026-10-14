package httpadapter

import (
	"fmt"
	"net/http"

	"real-city/backend/internal/adapter/http/middleware"
	wsadapter "real-city/backend/internal/adapter/ws"
)

func metrics(metrics *middleware.HTTPMetrics, realtime *wsadapter.Gateway) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		_ = r
		w.Header().Set("Content-Type", "text/plain; version=0.0.4")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("real_city_http_ready 1\n"))
		for _, sample := range metrics.Samples() {
			labels := fmt.Sprintf(
				`method=%q,route=%q,status_class=%q`,
				sample.Method,
				sample.Route,
				sample.StatusClass,
			)
			_, _ = fmt.Fprintf(w, "real_city_http_requests_total{%s} %d\n", labels, sample.Count)
			_, _ = fmt.Fprintf(w, "real_city_http_request_duration_ms_sum{%s} %d\n", labels, sample.DurationMillis)
			_, _ = fmt.Fprintf(w, "real_city_http_response_bytes_sum{%s} %d\n", labels, sample.ResponseBytes)
		}
		if realtime != nil {
			stats := realtime.Stats()
			_, _ = fmt.Fprintf(w, "real_city_ws_connections %d\n", stats.Connections)
			_, _ = fmt.Fprintf(w, "real_city_ws_chunk_subscriptions %d\n", stats.ChunkSubscriptions)
			_, _ = fmt.Fprintf(w, "real_city_ws_private_subscriptions %d\n", stats.PrivateSubscriptions)
			_, _ = fmt.Fprintf(w, "real_city_ws_alliance_subscriptions %d\n", stats.AllianceSubscriptions)
			_, _ = fmt.Fprintf(w, "real_city_ws_events_sent_total %d\n", stats.EventsSent)
			_, _ = fmt.Fprintf(w, "real_city_ws_fanout_total %d\n", stats.FanoutTotal)
			_, _ = fmt.Fprintf(w, "real_city_ws_messages_dropped_total %d\n", stats.Drops)
		}
	}
}

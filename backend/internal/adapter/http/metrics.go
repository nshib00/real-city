package httpadapter

import (
	"database/sql"
	"net/http"
	"strconv"

	"real-city/backend/internal/adapter/http/middleware"
	wsadapter "real-city/backend/internal/adapter/ws"
	"real-city/backend/internal/observability"
)

func metrics(metrics *middleware.HTTPMetrics, realtime *wsadapter.Gateway, pool *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
		out := observability.Writer{Out: w}
		out.Family("real_city_http_ready", "Metrics handler is responding; dependencies are not checked.", "gauge")
		out.Sample("real_city_http_ready", nil, 1)
		samples := metrics.Samples()
		out.Family("real_city_http_requests_total", "Completed HTTP requests excluding metrics and realtime.", "counter")
		for _, sample := range samples {
			out.Sample("real_city_http_requests_total", httpLabels(sample), float64(sample.Count))
		}
		out.Family("real_city_http_request_duration_seconds", "HTTP request duration in seconds.", "histogram")
		for _, sample := range samples {
			for i, bound := range middleware.DurationBuckets {
				labels := httpLabels(sample)
				labels["le"] = strconv.FormatFloat(bound, 'g', -1, 64)
				out.Sample("real_city_http_request_duration_seconds_bucket", labels, float64(sample.Buckets[i]))
			}
			labels := httpLabels(sample)
			labels["le"] = "+Inf"
			out.Sample("real_city_http_request_duration_seconds_bucket", labels, float64(sample.Count))
			out.Sample("real_city_http_request_duration_seconds_sum", httpLabels(sample), sample.DurationSeconds)
			out.Sample("real_city_http_request_duration_seconds_count", httpLabels(sample), float64(sample.Count))
		}
		out.Family("real_city_http_requests_in_flight", "HTTP requests currently in progress, excluding metrics and realtime.", "gauge")
		out.Sample("real_city_http_requests_in_flight", nil, float64(metrics.InFlight()))
		out.Family("real_city_http_response_bytes_total", "HTTP response body bytes.", "counter")
		for _, sample := range samples {
			out.Sample("real_city_http_response_bytes_total", httpLabels(sample), float64(sample.ResponseBytes))
		}
		// Compatibility series; remove after all dashboards use the new names.
		out.Family("real_city_http_request_duration_ms_sum", "Legacy sum of truncated HTTP duration milliseconds.", "counter")
		for _, sample := range samples {
			out.Sample("real_city_http_request_duration_ms_sum", httpLabels(sample), float64(sample.DurationMillis))
		}
		out.Family("real_city_http_response_bytes_sum", "Legacy HTTP response body byte sum.", "counter")
		for _, sample := range samples {
			out.Sample("real_city_http_response_bytes_sum", httpLabels(sample), float64(sample.ResponseBytes))
		}
		writeWSMetrics(out, realtime)
		observability.WriteDB(out, pool)
		observability.WriteSimulation(out)
		observability.WriteQueues(out)
		observability.WriteRuntime(out)
	}
}

func httpLabels(sample middleware.HTTPMetricSample) map[string]string {
	return map[string]string{"method": sample.Method, "route": sample.Route, "status_class": sample.StatusClass}
}

func writeWSMetrics(out observability.Writer, realtime *wsadapter.Gateway) {
	if realtime == nil {
		return
	}
	stats := realtime.Stats()
	out.Family("real_city_ws_connections", "Active WebSocket connections.", "gauge")
	out.Sample("real_city_ws_connections", nil, float64(stats.Connections))
	out.Family("real_city_ws_chunk_subscriptions", "Active chunk subscriptions.", "gauge")
	out.Sample("real_city_ws_chunk_subscriptions", nil, float64(stats.ChunkSubscriptions))
	out.Family("real_city_ws_private_subscriptions", "Active private subscriptions.", "gauge")
	out.Sample("real_city_ws_private_subscriptions", nil, float64(stats.PrivateSubscriptions))
	out.Family("real_city_ws_alliance_subscriptions", "Active alliance subscriptions.", "gauge")
	out.Sample("real_city_ws_alliance_subscriptions", nil, float64(stats.AllianceSubscriptions))
	out.Family("real_city_ws_events_sent_total", "Events received by gateway from EventBus.", "counter")
	out.Sample("real_city_ws_events_sent_total", nil, float64(stats.EventsSent))
	out.Family("real_city_ws_fanout_total", "Recipients selected for events before enqueue.", "counter")
	out.Sample("real_city_ws_fanout_total", nil, float64(stats.FanoutTotal))
	out.Family("real_city_ws_fanout_size", "Recipients selected per EventBus event.", "histogram")
	for i, bound := range wsadapter.FanoutBuckets {
		out.Sample("real_city_ws_fanout_size_bucket", map[string]string{"le": strconv.FormatFloat(bound, 'g', -1, 64)}, float64(stats.Transport.FanoutBuckets[i]))
	}
	out.Sample("real_city_ws_fanout_size_bucket", map[string]string{"le": "+Inf"}, float64(stats.EventsSent))
	out.Sample("real_city_ws_fanout_size_sum", nil, float64(stats.FanoutTotal))
	out.Sample("real_city_ws_fanout_size_count", nil, float64(stats.EventsSent))
	out.Family("real_city_ws_messages_dropped_total", "Event messages not enqueued.", "counter")
	out.Sample("real_city_ws_messages_dropped_total", nil, float64(stats.Drops))
	t := stats.Transport
	out.Family("real_city_ws_upgrades_total", "WebSocket upgrade attempts by bounded result.", "counter")
	for _, entry := range []struct {
		result string
		count  uint64
	}{{"ok", t.UpgradesOK}, {"auth_error", t.UpgradeAuthFailures}, {"handshake_error", t.UpgradeHandshakeFailures}, {"transport_error", t.UpgradeTransportFailures}} {
		out.Sample("real_city_ws_upgrades_total", map[string]string{"result": entry.result}, float64(entry.count))
	}
	out.Family("real_city_ws_messages_enqueued_total", "Messages queued for a WebSocket connection, including acknowledgments.", "counter")
	out.Sample("real_city_ws_messages_enqueued_total", nil, float64(t.Enqueued))
	out.Family("real_city_ws_messages_delivered_total", "Messages written successfully to a WebSocket connection.", "counter")
	out.Sample("real_city_ws_messages_delivered_total", nil, float64(t.Delivered))
	out.Family("real_city_ws_write_errors_total", "WebSocket frame write errors.", "counter")
	out.Sample("real_city_ws_write_errors_total", nil, float64(t.WriteErrors))
	out.Family("real_city_ws_slow_consumers_total", "Connections closed because their send queue filled.", "counter")
	out.Sample("real_city_ws_slow_consumers_total", nil, float64(t.SlowConsumers))
	out.Family("real_city_ws_send_queue_depth", "Queued messages across active WebSocket connections.", "gauge")
	out.Sample("real_city_ws_send_queue_depth", nil, float64(t.SendQueueDepth))
	out.Family("real_city_ws_send_queue_capacity", "Total queue capacity across active WebSocket connections.", "gauge")
	out.Sample("real_city_ws_send_queue_capacity", nil, float64(t.SendQueueCapacity))
}

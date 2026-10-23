package observability

import (
	"database/sql"
	"net/http"
)

// WorkerHandler exposes metrics for a standalone worker on its private listener.
func WorkerHandler(pool *sql.DB) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /metrics", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
		out := Writer{Out: w}
		WriteDB(out, pool)
		WriteSimulation(out)
		WriteQueues(out)
		WriteRuntime(out)
	})
	return mux
}

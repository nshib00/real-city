package postgres

import (
	"time"

	"real-city/backend/internal/observability"
)

// observe records one logical repository operation. Callers use distinct names for
// nested operations so a single call is not counted twice under the same name.
func observe(operation string, started time.Time, err *error) {
	observability.ObserveDB(operation, started, *err)
}

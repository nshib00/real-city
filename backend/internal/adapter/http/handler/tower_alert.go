package handler

import (
	"net/http"
	"time"

	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type TowerAlertHandler struct{ alerts service.TowerAlertRepository }

func NewTowerAlertHandler(alerts service.TowerAlertRepository) *TowerAlertHandler {
	return &TowerAlertHandler{alerts: alerts}
}

func (h *TowerAlertHandler) List(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	if h.alerts == nil {
		writeJSON(w, http.StatusServiceUnavailable, envelope{"error": "tower alert history unavailable"})
		return
	}
	var before time.Time
	beforeID := r.URL.Query().Get("before_id")
	if raw := r.URL.Query().Get("before"); raw != "" {
		parsed, err := time.Parse(time.RFC3339Nano, raw)
		if err != nil || beforeID == "" {
			writeError(w, apperror.New(apperror.BadRequest, "before requires an RFC3339 timestamp and before_id"))
			return
		}
		before = parsed
	} else if beforeID != "" {
		writeError(w, apperror.New(apperror.BadRequest, "before_id requires before"))
		return
	}
	items, err := h.alerts.ListForPlayer(r.Context(), playerID, queryLimit(r, 50), before, beforeID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"alerts": items})
}

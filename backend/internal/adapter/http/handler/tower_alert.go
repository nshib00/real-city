package handler

import (
	"net/http"
	"time"

	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/domain/alliance"
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
	items, err := h.alerts.ListHistoryForPlayer(r.Context(), playerID, queryLimit(r, 50), before, beforeID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"alerts": items})
}

func (h *TowerAlertHandler) PutShare(w http.ResponseWriter, r *http.Request) {
	if h.alerts == nil { writeJSON(w, http.StatusServiceUnavailable, envelope{"error":"tower sharing unavailable"}); return }
	actor, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var input struct {
		AllianceID string `json:"alliance_id"`
	}
	if err := decodeJSON(r, &input); err != nil {
		writeError(w, err)
		return
	}
	if input.AllianceID == "" {
		writeError(w, apperror.New(apperror.Validation, "alliance_id is required"))
		return
	}
	if err := h.alerts.SetShare(r.Context(), r.PathValue("id"), actor, alliance.ID(input.AllianceID), true); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"enabled": true, "alliance_id": input.AllianceID})
}

func (h *TowerAlertHandler) DeleteShare(w http.ResponseWriter, r *http.Request) {
	if h.alerts == nil { writeJSON(w, http.StatusServiceUnavailable, envelope{"error":"tower sharing unavailable"}); return }
	actor, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	if err := h.alerts.SetShare(r.Context(), r.PathValue("id"), actor, "", false); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"enabled": false})
}

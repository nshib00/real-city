package handler

import (
	"net/http"

	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type RaidHandler struct{ raids *service.RaidService }

func NewRaidHandler(raids *service.RaidService) *RaidHandler { return &RaidHandler{raids: raids} }

func (h *RaidHandler) List(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	items, err := h.raids.List(r.Context(), playerID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"raids": items})
}

func (h *RaidHandler) Start(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var req struct {
		TargetBuildingID string `json:"target_building_id"`
	}
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.raids.Start(r.Context(), playerID, building.ID(req.TargetBuildingID))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, envelope{"raid": item})
}

package handler

import (
	"net/http"
	"strconv"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type PlayerHandler struct {
	players *service.PlayerService
}

func NewPlayerHandler(players *service.PlayerService) *PlayerHandler {
	return &PlayerHandler{players: players}
}

func (h *PlayerHandler) Me(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "authenticated player is required"))
		return
	}
	p, err := h.players.GetMe(r.Context(), playerID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, dto.Player(p))
}

func (h *PlayerHandler) Public(w http.ResponseWriter, r *http.Request) {
	p, err := h.players.GetPublic(r.Context(), player.ID(r.PathValue("id")))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, dto.PublicPlayer(p))
}

func (h *PlayerHandler) UpdatePresence(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "authenticated player is required"))
		return
	}
	var req struct {
		TileX int `json:"tile_x"`
		TileY int `json:"tile_y"`
	}
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	if err := h.players.UpdatePresence(r.Context(), playerID, req.TileX, req.TileY); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"status": "ok"})
}

func (h *PlayerHandler) NearbyPresence(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "authenticated player is required"))
		return
	}
	x, xErr := strconv.Atoi(r.URL.Query().Get("x"))
	y, yErr := strconv.Atoi(r.URL.Query().Get("y"))
	radius, radiusErr := strconv.Atoi(r.URL.Query().Get("radius"))
	if xErr != nil || yErr != nil || radiusErr != nil {
		writeError(w, apperror.New(apperror.Validation, "invalid presence viewport"))
		return
	}
	items, err := h.players.NearbyPresence(r.Context(), playerID, x, y, radius)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"players": items})
}

func (h *PlayerHandler) UpdateMe(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "authenticated player is required"))
		return
	}
	var req dto.UpdateProfileRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	p, err := h.players.UpdateProfile(r.Context(), playerID, service.UpdateProfileInput{
		DisplayName: req.DisplayName,
		CityName:    req.CityName,
		AvatarURL:   req.AvatarURL,
		Settings:    req.Settings,
	})
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, dto.Player(p))
}

func (h *PlayerHandler) ChangePassword(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "authenticated player is required"))
		return
	}
	var req dto.ChangePasswordRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	if err := h.players.ChangePassword(r.Context(), playerID, req.CurrentPassword, req.NewPassword); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"status": "ok"})
}

func (h *PlayerHandler) DeleteMe(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "authenticated player is required"))
		return
	}
	if err := h.players.DeleteMe(r.Context(), playerID); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"status": "ok"})
}

package handler

import (
	"net/http"
	"runtime"

	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
)

type AdminHandler struct{ service *service.AdminService }

func (h *AdminHandler) ChangeAccount(w http.ResponseWriter, r *http.Request) {
	id, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var input struct {
		Status player.Status `json:"status"`
		Role   player.Role   `json:"role"`
		Reason string        `json:"reason"`
	}
	if err := decodeJSON(r, &input); err != nil {
		writeError(w, err)
		return
	}
	if err := h.service.ChangeAccount(r.Context(), id, player.ID(r.PathValue("id")), input.Status, input.Role, input.Reason); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"status": "ok"})
}

func (h *AdminHandler) AccountAudit(w http.ResponseWriter, r *http.Request) {
	id, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	items, err := h.service.AccountAudit(r.Context(), id, queryLimit(r, 100))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"actions": items})
}

func NewAdminHandler(s *service.AdminService) *AdminHandler { return &AdminHandler{s} }
func (h *AdminHandler) Status(w http.ResponseWriter, r *http.Request) {
	id, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	if err := h.service.Authorize(r.Context(), id); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"status": "ok", "goroutines": runtime.NumGoroutine()})
}
func (h *AdminHandler) Players(w http.ResponseWriter, r *http.Request) {
	id, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	items, err := h.service.Players(r.Context(), id, queryLimit(r, 100))
	if err != nil {
		writeError(w, err)
		return
	}
	// Deliberately omit email, password hashes and profile settings from this list.
	rows := []map[string]any{}
	for _, p := range items {
		rows = append(rows, map[string]any{"id": p.ID, "name": p.Name, "status": p.Status, "role": p.Role, "created_at": p.CreatedAt})
	}
	writeJSON(w, http.StatusOK, envelope{"players": rows})
}
func (h *AdminHandler) Flagged(w http.ResponseWriter, r *http.Request) {
	id, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	items, err := h.service.Flagged(r.Context(), id, queryLimit(r, 100))
	if err != nil {
		writeError(w, err)
		return
	}
	rows := []map[string]any{}
	for _, m := range items {
		rows = append(rows, map[string]any{"id": m.ID, "channel": m.Channel, "author_id": m.AuthorID, "body": m.Body, "created_at": m.CreatedAt})
	}
	writeJSON(w, http.StatusOK, envelope{"messages": rows})
}
func (h *AdminHandler) Audit(w http.ResponseWriter, r *http.Request) {
	id, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	items, err := h.service.Audit(r.Context(), id, queryLimit(r, 100))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"actions": items})
}
func (h *AdminHandler) Moderate(w http.ResponseWriter, r *http.Request) {
	id, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var input struct {
		Action string `json:"action"`
		Reason string `json:"reason"`
	}
	if err := decodeJSON(r, &input); err != nil {
		writeError(w, err)
		return
	}
	if err := h.service.Moderate(r.Context(), id, chat.MessageID(r.PathValue("id")), input.Action, input.Reason); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"status": "ok"})
}

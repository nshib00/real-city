package handler

import (
	"net/http"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type CombatHandler struct{ combat *service.CombatService }

func NewCombatHandler(combat *service.CombatService) *CombatHandler {
	return &CombatHandler{combat: combat}
}

func (h *CombatHandler) BuildingWeapon(w http.ResponseWriter, r *http.Request) {
	actor, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var input struct {
		Weapon economy.ResourceType `json:"weapon"`
	}
	if err := decodeJSON(r, &input); err != nil {
		writeError(w, err)
		return
	}
	attack, err := h.combat.UseBuildingWeapon(r.Context(), building.ID(r.PathValue("id")), actor, input.Weapon, r.Header.Get("Idempotency-Key"))
	if err != nil {
		writeError(w, err)
		return
	}
	response := envelope{"attack": attack}
	if attack.Building != nil {
		response["building"] = dto.Building(*attack.Building)
	}
	writeJSON(w, http.StatusAccepted, response)
}

func (h *CombatHandler) CreateMonster(w http.ResponseWriter, r *http.Request) {
	actor, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var input struct {
		TargetBuildingID building.ID `json:"target_building_id"`
	}
	if err := decodeJSON(r, &input); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.combat.CreateMonster(r.Context(), actor, input.TargetBuildingID, r.Header.Get("Idempotency-Key"))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, envelope{"monster": dto.Monster(item)})
}

func (h *CombatHandler) Rules(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, envelope{"rules": catalog.CombatRules()})
}

func (h *CombatHandler) History(w http.ResponseWriter, r *http.Request) {
	id, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	items, err := h.combat.History(r.Context(), id, queryLimit(r, 50))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"records": items})
}

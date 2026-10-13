package handler

import (
	"net/http"
	"strconv"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type MonsterHandler struct {
	monsters *service.MonsterService
	combat   *service.CombatService
	threats  *service.ThreatService
}

func NewMonsterHandler(monsters *service.MonsterService, combat *service.CombatService, threats *service.ThreatService) *MonsterHandler {
	return &MonsterHandler{monsters: monsters, combat: combat, threats: threats}
}

func (h *MonsterHandler) Catalog(w http.ResponseWriter, r *http.Request) {
	items, err := h.monsters.Catalog(r.Context())
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"monsters": dto.MonsterSpecs(items)})
}

func (h *MonsterHandler) List(w http.ResponseWriter, r *http.Request) {
	center, radius := viewportParams(r)
	items, err := h.monsters.List(r.Context(), center, radius)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"monsters": dto.Monsters(items)})
}

func (h *MonsterHandler) Get(w http.ResponseWriter, r *http.Request) {
	item, err := h.monsters.Get(r.Context(), monster.ID(r.PathValue("id")))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"monster": dto.Monster(item)})
}

func (h *MonsterHandler) Attack(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	item, rewards, err := h.combat.AttackMonster(r.Context(), monster.ID(r.PathValue("id")), playerID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"monster": dto.Monster(item), "rewards": rewards})
}

func (h *MonsterHandler) Threats(w http.ResponseWriter, r *http.Request) {
	center, radius := viewportParams(r)
	items, err := h.threats.Around(r.Context(), center, radius)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"threats": dto.Threats(items)})
}

func (h *MonsterHandler) Loot(w http.ResponseWriter, r *http.Request) {
	center, radius := viewportParams(r)
	items, err := h.monsters.ListLoot(r.Context(), center, radius)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"loot": dto.LootDrops(items)})
}

func (h *MonsterHandler) ClaimLoot(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	drop, inventory, err := h.monsters.ClaimLoot(r.Context(), monster.LootDropID(r.PathValue("id")), playerID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"loot": dto.LootDrop(drop), "inventory": dto.Inventory(inventory)})
}

func viewportParams(r *http.Request) (world.Coord, int) {
	x, _ := strconv.Atoi(r.URL.Query().Get("x"))
	y, _ := strconv.Atoi(r.URL.Query().Get("y"))
	radius, _ := strconv.Atoi(r.URL.Query().Get("radius"))
	if radius <= 0 {
		radius = 24
	}
	if radius > 96 {
		radius = 96
	}
	return world.Coord{X: x, Y: y}, radius
}

package handler

import (
	"net/http"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type BuildingHandler struct {
	buildings *service.BuildingService
}

func NewBuildingHandler(buildings *service.BuildingService) *BuildingHandler {
	return &BuildingHandler{buildings: buildings}
}

func (h *BuildingHandler) Catalog(w http.ResponseWriter, r *http.Request) {
	items, err := h.buildings.Catalog(r.Context())
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"buildings": dto.BuildingCatalog(items)})
}

func (h *BuildingHandler) List(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	items, err := h.buildings.ListPlayer(r.Context(), playerID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"buildings": dto.Buildings(items)})
}

func (h *BuildingHandler) Place(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var req dto.PlaceBuildingRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.buildings.Place(r.Context(), service.PlaceBuildingInput{
		PlayerID: playerID,
		Type:     building.Type(req.Type),
		Tile:     world.Coord{X: req.TileX, Y: req.TileY},
	})
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, envelope{"building": dto.Building(item)})
}

func (h *BuildingHandler) Get(w http.ResponseWriter, r *http.Request) {
	item, err := h.buildings.Get(r.Context(), building.ID(r.PathValue("id")))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"building": dto.Building(item)})
}

func (h *BuildingHandler) Patch(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var req dto.PatchBuildingRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	id := building.ID(r.PathValue("id"))
	switch req.Action {
	case "complete":
		item, err := h.buildings.Complete(r.Context(), id, playerID)
		if err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"building": dto.Building(item)})
	case "rush_complete":
		item, inventory, crystalCost, err := h.buildings.RushComplete(r.Context(), id, playerID)
		if err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"building": dto.Building(item), "inventory": dto.Inventory(inventory), "rush": dto.RushCompletionResponse{CrystalCost: crystalCost}})
	case "cancel":
		if err := h.buildings.Cancel(r.Context(), id, playerID); err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"status": "ok"})
	case "repair":
		item, err := h.buildings.Repair(r.Context(), id, playerID)
		if err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"building": dto.Building(item)})
	case "upgrade":
		item, err := h.buildings.Upgrade(r.Context(), id, playerID)
		if err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"building": dto.Building(item)})
	default:
		writeError(w, apperror.WithFields(apperror.Validation, "unsupported building action", map[string]string{"action": "must be complete, rush_complete, cancel, repair or upgrade"}))
	}
}

func (h *BuildingHandler) Delete(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	if err := h.buildings.Demolish(r.Context(), building.ID(r.PathValue("id")), playerID); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"status": "ok"})
}

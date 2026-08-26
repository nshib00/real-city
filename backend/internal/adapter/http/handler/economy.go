package handler

import (
	"net/http"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type EconomyHandler struct {
	economy    *service.EconomyService
	resources  *service.ResourceService
	production *service.ProductionService
	fields     *service.FieldService
	population *service.PopulationService
}

func NewEconomyHandler(economyService *service.EconomyService, resources *service.ResourceService, production *service.ProductionService, fields *service.FieldService, population *service.PopulationService) *EconomyHandler {
	return &EconomyHandler{economy: economyService, resources: resources, production: production, fields: fields, population: population}
}

func (h *EconomyHandler) Inventory(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	item, err := h.economy.Inventory(r.Context(), playerID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"inventory": dto.Inventory(item)})
}

func (h *EconomyHandler) Transactions(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	items, err := h.economy.Transactions(r.Context(), playerID, 20)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"transactions": dto.Transactions(items)})
}

func (h *EconomyHandler) Population(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	item, err := h.population.Summary(r.Context(), playerID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"population": dto.Population(item)})
}

func (h *EconomyHandler) ResourceNodes(w http.ResponseWriter, r *http.Request) {
	items, err := h.resources.List(r.Context())
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"nodes": dto.ResourceNodes(items)})
}

func (h *EconomyHandler) PatchResourceNode(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var req dto.PatchResourceNodeRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	id := economy.NodeID(r.PathValue("id"))
	switch req.Action {
	case "claim":
		node, err := h.resources.Claim(r.Context(), id, playerID)
		if err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"node": dto.ResourceNode(node)})
	case "harvest":
		node, inventory, err := h.resources.Harvest(r.Context(), id, playerID)
		if err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"node": dto.ResourceNode(node), "inventory": dto.Inventory(inventory)})
	default:
		writeError(w, apperror.WithFields(apperror.Validation, "unsupported resource node action", map[string]string{"action": "must be claim or harvest"}))
	}
}

func (h *EconomyHandler) ProductionRecipes(w http.ResponseWriter, r *http.Request) {
	items, err := h.production.Recipes(r.Context())
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"recipes": dto.ProductionRecipes(items)})
}

func (h *EconomyHandler) ProductionJobs(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	items, err := h.production.List(r.Context(), playerID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"jobs": dto.ProductionJobs(items)})
}

func (h *EconomyHandler) StartProduction(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var req dto.StartProductionRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	job, inventory, err := h.production.Start(r.Context(), playerID, req.BuildingID, req.RecipeID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, envelope{"job": dto.ProductionJob(job), "inventory": dto.Inventory(inventory)})
}

func (h *EconomyHandler) PatchProduction(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var req dto.PatchProductionRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	id := economy.ProductionJobID(r.PathValue("id"))
	switch req.Action {
	case "complete":
		job, inventory, err := h.production.Complete(r.Context(), playerID, id)
		if err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"job": dto.ProductionJob(job), "inventory": dto.Inventory(inventory)})
	case "cancel":
		job, err := h.production.Cancel(r.Context(), playerID, id)
		if err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"job": dto.ProductionJob(job)})
	default:
		writeError(w, apperror.WithFields(apperror.Validation, "unsupported production action", map[string]string{"action": "must be complete or cancel"}))
	}
}

func (h *EconomyHandler) HarvestField(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var req dto.HarvestFieldRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	inventory, err := h.fields.HarvestWindleaf(r.Context(), playerID, req.Super)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"inventory": dto.Inventory(inventory)})
}

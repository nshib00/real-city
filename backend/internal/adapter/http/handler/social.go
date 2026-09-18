package handler

import (
	"net/http"
	"strconv"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type AllianceHandler struct {
	service *service.AllianceService
}

func NewAllianceHandler(service *service.AllianceService) *AllianceHandler {
	return &AllianceHandler{service: service}
}

func (h *AllianceHandler) Profile(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	item, err := h.service.Profile(r.Context(), playerID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"profile": dto.AllianceProfile(item)})
}

func (h *AllianceHandler) Create(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var req dto.CreateAllianceRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.service.Create(r.Context(), playerID, req.Name)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, envelope{"profile": dto.AllianceProfile(item)})
}

func (h *AllianceHandler) Invite(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var req dto.InviteAllianceRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.service.Invite(r.Context(), playerID, player.ID(req.PlayerID))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, envelope{"invite": dto.AllianceInvite(item)})
}

func (h *AllianceHandler) RespondInvite(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var req dto.RespondInviteRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.service.RespondInvite(r.Context(), playerID, alliance.InviteID(r.PathValue("id")), req.Accept)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"profile": dto.AllianceProfile(item)})
}

func (h *AllianceHandler) SetRole(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var req dto.SetAllianceRoleRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.service.SetRole(r.Context(), playerID, player.ID(req.PlayerID), alliance.Role(req.Role), req.Treasurer)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"profile": dto.AllianceProfile(item)})
}

func (h *AllianceHandler) Donate(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var req dto.DonateAllianceRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.service.Donate(r.Context(), playerID, economy.ResourceType(req.Resource), req.Amount)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"profile": dto.AllianceProfile(item)})
}

func (h *AllianceHandler) UpgradeBuff(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var req dto.UpgradeAllianceBuffRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.service.UpgradeBuff(r.Context(), playerID, alliance.BuffID(req.BuffID))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"profile": dto.AllianceProfile(item)})
}

func (h *AllianceHandler) AddTerritoryAid(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var req dto.AddTerritoryAidRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.service.AddTerritoryAid(r.Context(), playerID, req.TargetType, req.TargetID)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, envelope{"aid": dto.TerritoryAidItems([]alliance.TerritoryAid{item})[0]})
}

type ChatHandler struct {
	service *service.ChatService
}

func NewChatHandler(service *service.ChatService) *ChatHandler {
	return &ChatHandler{service: service}
}

func (h *ChatHandler) List(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	limit := queryLimit(r, 50)
	items, err := h.service.List(r.Context(), playerID, chat.Channel(r.URL.Query().Get("channel")), limit)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"messages": dto.ChatMessages(items)})
}

func (h *ChatHandler) Send(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var req dto.SendChatMessageRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.service.Send(r.Context(), playerID, chat.Channel(req.Channel), player.ID(req.Recipient), req.Body)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, envelope{"message": dto.ChatMessage(item)})
}

type MarketHandler struct {
	service *service.MarketService
}

func NewMarketHandler(service *service.MarketService) *MarketHandler {
	return &MarketHandler{service: service}
}

func (h *MarketHandler) List(w http.ResponseWriter, r *http.Request) {
	items, err := h.service.List(r.Context(), queryLimit(r, 50))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"orders": dto.MarketOrders(items)})
}

func (h *MarketHandler) Create(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	var req dto.CreateMarketOrderRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	item, err := h.service.Create(r.Context(), playerID, market.Side(req.Side), economy.ResourceType(req.Resource), req.Amount, req.Price)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, envelope{"order": dto.MarketOrder(item)})
}

func (h *MarketHandler) Cancel(w http.ResponseWriter, r *http.Request) {
	playerID, ok := requirePlayerID(w, r)
	if !ok {
		return
	}
	item, err := h.service.Cancel(r.Context(), playerID, market.OrderID(r.PathValue("id")))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"order": dto.MarketOrder(item)})
}

func requirePlayerID(w http.ResponseWriter, r *http.Request) (player.ID, bool) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return "", false
	}
	return playerID, true
}

func queryLimit(r *http.Request, fallback int) int {
	value, err := strconv.Atoi(r.URL.Query().Get("limit"))
	if err != nil || value <= 0 {
		return fallback
	}
	if value > 200 {
		return 200
	}
	return value
}

package dto

import (
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/service"
)

type AllianceResponse struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	LeaderID    string    `json:"leader_id"`
	Level       int       `json:"level"`
	MemberLimit int       `json:"member_limit"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type AllianceMemberResponse struct {
	PlayerID  string    `json:"player_id"`
	Role      string    `json:"role"`
	Treasurer bool      `json:"treasurer"`
	JoinedAt  time.Time `json:"joined_at"`
}

type AllianceInviteResponse struct {
	ID          string     `json:"id"`
	AllianceID  string     `json:"alliance_id"`
	InviterID   string     `json:"inviter_id"`
	InviteeID   string     `json:"invitee_id"`
	Status      string     `json:"status"`
	CreatedAt   time.Time  `json:"created_at"`
	RespondedAt *time.Time `json:"responded_at"`
}

type TreasuryEntryResponse struct {
	ID          string    `json:"id"`
	PlayerID    string    `json:"player_id"`
	Kind        string    `json:"kind"`
	Resource    string    `json:"resource"`
	Amount      int       `json:"amount"`
	Description string    `json:"description"`
	CreatedAt   time.Time `json:"created_at"`
}

type AllianceBuffResponse struct {
	ID        string    `json:"id"`
	Level     int       `json:"level"`
	UpdatedAt time.Time `json:"updated_at"`
}

type TerritoryAidResponse struct {
	TargetType string    `json:"target_type"`
	TargetID   string    `json:"target_id"`
	PlayerID   string    `json:"player_id"`
	CreatedAt  time.Time `json:"created_at"`
}

type AllianceProfileResponse struct {
	Alliance *AllianceResponse        `json:"alliance"`
	Self     *AllianceMemberResponse  `json:"self"`
	Members  []AllianceMemberResponse `json:"members"`
	Invites  []AllianceInviteResponse `json:"invites"`
	Treasury []TreasuryEntryResponse  `json:"treasury"`
	Buffs    []AllianceBuffResponse   `json:"buffs"`
	Aid      []TerritoryAidResponse   `json:"aid"`
}

type CreateAllianceRequest struct {
	Name string `json:"name"`
}

type InviteAllianceRequest struct {
	PlayerID string `json:"player_id"`
}

type RespondInviteRequest struct {
	Accept bool `json:"accept"`
}

type SetAllianceRoleRequest struct {
	PlayerID  string `json:"player_id"`
	Role      string `json:"role"`
	Treasurer bool   `json:"treasurer"`
}

type DonateAllianceRequest struct {
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
}

type UpgradeAllianceBuffRequest struct {
	BuffID string `json:"buff_id"`
}

type AddTerritoryAidRequest struct {
	TargetType string `json:"target_type"`
	TargetID   string `json:"target_id"`
}

type ChatMessageResponse struct {
	ID         string    `json:"id"`
	Channel    string    `json:"channel"`
	AuthorID   string    `json:"author_id"`
	AllianceID string    `json:"alliance_id,omitempty"`
	Recipient  string    `json:"recipient,omitempty"`
	Body       string    `json:"body"`
	Flagged    bool      `json:"flagged"`
	CreatedAt  time.Time `json:"created_at"`
}

type SendChatMessageRequest struct {
	Channel   string `json:"channel"`
	Recipient string `json:"recipient"`
	Body      string `json:"body"`
}

type MarketOrderResponse struct {
	ID        string    `json:"id"`
	PlayerID  string    `json:"player_id"`
	Side      string    `json:"side"`
	Resource  string    `json:"resource"`
	Amount    int       `json:"amount"`
	Price     int       `json:"price"`
	Fee       int       `json:"fee"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type CreateMarketOrderRequest struct {
	Side     string `json:"side"`
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
	Price    int    `json:"price"`
}

func AllianceProfile(item service.AllianceProfile) AllianceProfileResponse {
	response := AllianceProfileResponse{
		Members:  AllianceMembers(item.Members),
		Invites:  AllianceInvites(item.Invites),
		Treasury: TreasuryEntries(item.Treasury),
		Buffs:    AllianceBuffs(item.Buffs),
		Aid:      TerritoryAidItems(item.Aid),
	}
	if item.Alliance.ID != "" {
		allianceResponse := Alliance(item.Alliance)
		self := AllianceMember(item.Self)
		response.Alliance = &allianceResponse
		response.Self = &self
	}
	return response
}

func Alliance(item alliance.Alliance) AllianceResponse {
	return AllianceResponse{ID: string(item.ID), Name: item.Name, Description: item.Description, LeaderID: string(item.LeaderID), Level: item.Level, MemberLimit: alliance.MemberLimit(item.Level), CreatedAt: item.CreatedAt, UpdatedAt: item.UpdatedAt}
}

func AllianceMember(item alliance.Membership) AllianceMemberResponse {
	return AllianceMemberResponse{PlayerID: string(item.PlayerID), Role: string(item.Role), Treasurer: item.Treasurer, JoinedAt: item.JoinedAt}
}

func AllianceMembers(items []alliance.Membership) []AllianceMemberResponse {
	result := make([]AllianceMemberResponse, 0, len(items))
	for _, item := range items {
		result = append(result, AllianceMember(item))
	}
	return result
}

func AllianceInvite(item alliance.Invite) AllianceInviteResponse {
	return AllianceInviteResponse{ID: string(item.ID), AllianceID: string(item.AllianceID), InviterID: string(item.InviterID), InviteeID: string(item.InviteeID), Status: string(item.Status), CreatedAt: item.CreatedAt, RespondedAt: item.RespondedAt}
}

func AllianceInvites(items []alliance.Invite) []AllianceInviteResponse {
	result := make([]AllianceInviteResponse, 0, len(items))
	for _, item := range items {
		result = append(result, AllianceInvite(item))
	}
	return result
}

func TreasuryEntries(items []alliance.TreasuryEntry) []TreasuryEntryResponse {
	result := make([]TreasuryEntryResponse, 0, len(items))
	for _, item := range items {
		result = append(result, TreasuryEntryResponse{ID: string(item.ID), PlayerID: string(item.PlayerID), Kind: string(item.Kind), Resource: string(item.Resource), Amount: item.Amount, Description: item.Description, CreatedAt: item.CreatedAt})
	}
	return result
}

func AllianceBuffs(items []alliance.Buff) []AllianceBuffResponse {
	result := make([]AllianceBuffResponse, 0, len(items))
	for _, item := range items {
		result = append(result, AllianceBuffResponse{ID: string(item.ID), Level: item.Level, UpdatedAt: item.UpdatedAt})
	}
	return result
}

func TerritoryAidItems(items []alliance.TerritoryAid) []TerritoryAidResponse {
	result := make([]TerritoryAidResponse, 0, len(items))
	for _, item := range items {
		result = append(result, TerritoryAidResponse{TargetType: item.TargetType, TargetID: item.TargetID, PlayerID: string(item.PlayerID), CreatedAt: item.CreatedAt})
	}
	return result
}

func ChatMessage(item chat.Message) ChatMessageResponse {
	return ChatMessageResponse{ID: string(item.ID), Channel: string(item.Channel), AuthorID: string(item.AuthorID), AllianceID: string(item.AllianceID), Recipient: string(item.Recipient), Body: item.Body, Flagged: item.Flagged, CreatedAt: item.CreatedAt}
}

func ChatMessages(items []chat.Message) []ChatMessageResponse {
	result := make([]ChatMessageResponse, 0, len(items))
	for _, item := range items {
		result = append(result, ChatMessage(item))
	}
	return result
}

func MarketOrder(item market.Order) MarketOrderResponse {
	return MarketOrderResponse{ID: string(item.ID), PlayerID: string(item.PlayerID), Side: string(item.Side), Resource: string(item.Resource), Amount: item.Amount, Price: item.Price, Fee: item.Fee, Status: string(item.Status), CreatedAt: item.CreatedAt, UpdatedAt: item.UpdatedAt}
}

func MarketOrders(items []market.Order) []MarketOrderResponse {
	result := make([]MarketOrderResponse, 0, len(items))
	for _, item := range items {
		result = append(result, MarketOrder(item))
	}
	return result
}

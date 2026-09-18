package alliance

import (
	"strings"
	"time"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

type ID string
type InviteID string
type LedgerID string
type BuffID string
type Role string
type InviteStatus string
type LedgerKind string

const (
	RoleLeader  Role = "leader"
	RoleDeputy  Role = "deputy"
	RoleOfficer Role = "officer"
	RoleMember  Role = "member"

	InvitePending  InviteStatus = "pending"
	InviteAccepted InviteStatus = "accepted"
	InviteDeclined InviteStatus = "declined"

	LedgerDonation LedgerKind = "donation"
	LedgerSpend    LedgerKind = "spend"
)

type Alliance struct {
	ID          ID
	Name        string
	Description string
	LeaderID    player.ID
	Level       int
	CreatedAt   time.Time
	UpdatedAt   time.Time
}

type Membership struct {
	AllianceID ID
	PlayerID   player.ID
	Role       Role
	Treasurer  bool
	JoinedAt   time.Time
}

type Invite struct {
	ID          InviteID
	AllianceID  ID
	InviterID   player.ID
	InviteeID   player.ID
	Status      InviteStatus
	CreatedAt   time.Time
	RespondedAt *time.Time
}

type TreasuryEntry struct {
	ID          LedgerID
	AllianceID  ID
	PlayerID    player.ID
	Kind        LedgerKind
	Resource    economy.ResourceType
	Amount      int
	Description string
	CreatedAt   time.Time
}

type Buff struct {
	AllianceID ID
	ID         BuffID
	Level      int
	UpdatedAt  time.Time
}

type TerritoryAid struct {
	AllianceID ID
	TargetType string
	TargetID   string
	PlayerID   player.ID
	CreatedAt  time.Time
}

func NormalizeName(name string) string {
	return strings.Join(strings.Fields(strings.TrimSpace(name)), " ")
}

func MemberLimit(level int) int {
	switch {
	case level >= 3:
		return 35
	case level == 2:
		return 25
	default:
		return 15
	}
}

func CanManageMembers(role Role) bool {
	return role == RoleLeader || role == RoleDeputy || role == RoleOfficer
}

func CanSpendTreasury(m Membership) bool {
	return m.Role == RoleLeader || m.Treasurer
}

package chat

import (
	"strings"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/player"
)

type MessageID string
type Channel string

const (
	ChannelGlobal   Channel = "global"
	ChannelNearby   Channel = "nearby"
	ChannelAlliance Channel = "alliance"
	ChannelPrivate  Channel = "private"
)

type Message struct {
	ID         MessageID
	Channel    Channel
	AuthorID   player.ID
	AllianceID alliance.ID
	Recipient  player.ID
	Body       string
	Flagged    bool
	CreatedAt  time.Time
	// Nearby messages are private to the server-calculated audience at send time.
	Audience []player.ID
}

type Cursor struct {
	CreatedAt time.Time `json:"created_at"`
	ID        MessageID `json:"id"`
}

type ModerationAudit struct {
	ID        string    `json:"id"`
	ActorID   player.ID `json:"actor_id"`
	MessageID MessageID `json:"message_id"`
	Action    string    `json:"action"`
	Reason    string    `json:"reason"`
	CreatedAt time.Time `json:"created_at"`
}

func NormalizeBody(body string) string {
	return strings.Join(strings.Fields(strings.TrimSpace(body)), " ")
}

func ModerationFlag(body string) bool {
	lower := strings.ToLower(body)
	return strings.Contains(lower, "http://") || strings.Contains(lower, "https://") || strings.Contains(lower, "<script")
}

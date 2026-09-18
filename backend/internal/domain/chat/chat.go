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
}

func NormalizeBody(body string) string {
	return strings.Join(strings.Fields(strings.TrimSpace(body)), " ")
}

func ModerationFlag(body string) bool {
	lower := strings.ToLower(body)
	return strings.Contains(lower, "http://") || strings.Contains(lower, "https://") || strings.Contains(lower, "<script")
}

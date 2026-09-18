package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type ChatService struct {
	repo      ChatRepository
	alliances AllianceRepository
	log       *slog.Logger
	now       func() time.Time
}

func NewChatService(repo ChatRepository, alliances AllianceRepository, log *slog.Logger) *ChatService {
	return &ChatService{repo: repo, alliances: alliances, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *ChatService) List(ctx context.Context, playerID player.ID, channel chat.Channel, limit int) ([]chat.Message, error) {
	allianceID, err := s.allianceID(ctx, playerID, channel)
	if err != nil {
		return nil, err
	}
	return s.repo.ListMessages(ctx, playerID, channel, allianceID, limit)
}

func (s *ChatService) Send(ctx context.Context, playerID player.ID, channel chat.Channel, recipient player.ID, body string) (chat.Message, error) {
	body = chat.NormalizeBody(body)
	if len([]rune(body)) < 1 || len([]rune(body)) > 500 {
		return chat.Message{}, apperror.WithFields(apperror.Validation, "invalid chat message", map[string]string{"body": "must be 1-500 characters"})
	}
	if channel == chat.ChannelPrivate && recipient == "" {
		return chat.Message{}, apperror.New(apperror.Validation, "private message recipient is required")
	}
	allianceID, err := s.allianceID(ctx, playerID, channel)
	if err != nil {
		return chat.Message{}, err
	}
	msg := chat.Message{
		ID:         chat.MessageID(fmt.Sprintf("chat_%d", s.now().UnixNano())),
		Channel:    channel,
		AuthorID:   playerID,
		AllianceID: allianceID,
		Recipient:  recipient,
		Body:       body,
		Flagged:    chat.ModerationFlag(body),
		CreatedAt:  s.now(),
	}
	if err := s.repo.AddMessage(ctx, msg); err != nil {
		return chat.Message{}, err
	}
	s.log.Info("chat.message.created", "event", "chat.message.created", "player_id", playerID, "channel", channel, "flagged", msg.Flagged)
	return msg, nil
}

func (s *ChatService) allianceID(ctx context.Context, playerID player.ID, channel chat.Channel) (alliance.ID, error) {
	switch channel {
	case chat.ChannelGlobal, chat.ChannelNearby, chat.ChannelPrivate:
		return "", nil
	case chat.ChannelAlliance:
		item, _, err := s.alliances.FindByPlayer(ctx, playerID)
		if err != nil {
			return "", apperror.New(apperror.Forbidden, "alliance channel requires membership")
		}
		return item.ID, nil
	default:
		return "", apperror.New(apperror.Validation, "unsupported chat channel")
	}
}

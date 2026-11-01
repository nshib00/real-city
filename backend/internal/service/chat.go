package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type ChatService struct {
	repo      ChatRepository
	events    *EventBus
	uow       UnitOfWork
	alliances AllianceRepository
	log       *slog.Logger
	now       func() time.Time
	buildings BuildingRepository
}

func NewChatService(repo ChatRepository, alliances AllianceRepository, log *slog.Logger) *ChatService {
	return &ChatService{repo: repo, alliances: alliances, uow: snapshotUnitOfWork{[]any{repo}}, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *ChatService) SetBuildings(repo BuildingRepository) { s.buildings = repo }

func (s *ChatService) List(ctx context.Context, playerID player.ID, channel chat.Channel, limit int, before ...chat.Cursor) ([]chat.Message, error) {
	allianceID, err := s.allianceID(ctx, playerID, channel)
	if err != nil {
		return nil, err
	}
	if limit <= 0 || limit > 100 {
		limit = 100
	}
	return s.repo.ListMessages(ctx, playerID, channel, allianceID, limit, before...)
}

func (s *ChatService) send(ctx context.Context, playerID player.ID, channel chat.Channel, recipient player.ID, body string) (chat.Message, error) {
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
	if channel == chat.ChannelNearby {
		msg.Audience, err = s.nearbyAudience(ctx, playerID)
		if err != nil {
			return chat.Message{}, err
		}
	}
	if err := s.repo.AddMessage(ctx, msg); err != nil {
		return chat.Message{}, err
	}
	s.publishMessage(ctx, msg)
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
			return "", apperror.New(apperror.Forbidden, "Канал союза доступен только его участникам")
		}
		return item.ID, nil
	default:
		return "", apperror.New(apperror.Validation, "unsupported chat channel")
	}
}

func (s *ChatService) SetEventBus(events *EventBus) { s.events = events }
func (s *ChatService) publishMessage(ctx context.Context, msg chat.Message) {
	payload := ChatMessagePayload{msg}
	event := Event{Type: "chat.message.created", Payload: payload}
	switch msg.Channel {
	case chat.ChannelAlliance:
		members, err := s.alliances.ListMembers(ctx, msg.AllianceID)
		if err != nil {
			return
		}
		for _, m := range members {
			event.PlayerID = m.PlayerID
			publishEvent(ctx, s.events, event)
		}
	case chat.ChannelPrivate:
		event.PlayerID = msg.AuthorID
		publishEvent(ctx, s.events, event)
		if msg.Recipient != msg.AuthorID {
			event.PlayerID = msg.Recipient
			publishEvent(ctx, s.events, event)
		}
	case chat.ChannelNearby:
		for _, id := range msg.Audience {
			event.PlayerID = id
			publishEvent(ctx, s.events, event)
		}
	default:
		publishEvent(ctx, s.events, event)
	}
}

// A city is nearby if a living building is within 32 tiles of the sender's
// living buildings on the same map. Camera position cannot expand the audience.
func (s *ChatService) nearbyAudience(ctx context.Context, sender player.ID) ([]player.ID, error) {
	if s.buildings == nil {
		return nil, apperror.New(apperror.Conflict, "Локальный чат недоступен")
	}
	owned, err := s.buildings.ListByPlayer(ctx, sender)
	if err != nil {
		return nil, err
	}
	audience := []player.ID{sender}
	seen := map[player.ID]bool{sender: true}
	maps := map[string][]building.Building{}
	for _, source := range owned {
		if source.Health <= 0 || source.State == building.StateRuined {
			continue
		}
		items, ok := maps[source.MapID]
		if !ok {
			items, err = s.buildings.ListByMap(ctx, source.MapID)
			if err != nil {
				return nil, err
			}
			maps[source.MapID] = items
		}
		for _, target := range items {
			id := player.ID(target.OwnerID)
			if id == "" || seen[id] || target.Health <= 0 || target.State == building.StateRuined {
				continue
			}
			if wrappedTileDistance(source.Tile.X, target.Tile.X) <= 32 && wrappedTileDistance(source.Tile.Y, target.Tile.Y) <= 32 {
				seen[id] = true
				audience = append(audience, id)
			}
		}
	}
	return audience, nil
}

type ChatReadState struct {
	ReadAt time.Time `json:"read_at"`
	Unread int       `json:"unread"`
}

func (s *ChatService) ReadState(ctx context.Context, p player.ID, ch chat.Channel) (state ChatReadState, err error) {
	id, err := s.allianceID(ctx, p, ch)
	if err != nil {
		return state, err
	}
	state.ReadAt, err = s.repo.ReadAt(ctx, p, string(ch)+":"+string(id))
	if err != nil {
		return state, err
	}
	state.Unread, err = s.repo.CountUnread(ctx, p, ch, id, state.ReadAt)
	return
}
func (s *ChatService) MarkRead(ctx context.Context, p player.ID, ch chat.Channel, messageID chat.MessageID) (ChatReadState, error) {
	id, err := s.allianceID(ctx, p, ch)
	if err != nil {
		return ChatReadState{}, err
	}
	// Only a message actually delivered to this player's channel may advance its cursor.
	messages, err := s.repo.ListMessages(ctx, p, ch, id, 100)
	if err != nil {
		return ChatReadState{}, err
	}
	var at time.Time
	for _, m := range messages {
		if m.ID == messageID {
			at = m.CreatedAt
			break
		}
	}
	if at.IsZero() {
		return ChatReadState{}, apperror.New(apperror.Validation, "read cursor must reference a visible recent message")
	}
	if err = s.repo.SaveReadAt(ctx, p, string(ch)+":"+string(id), at); err != nil {
		return ChatReadState{}, err
	}
	state, err := s.ReadState(ctx, p, ch)
	if err == nil {
		publishEvent(ctx, s.events, Event{Type: "chat.read.updated", PlayerID: p, Payload: map[string]any{"channel": ch}})
	}
	return state, err
}

func (s *ChatService) SetUnitOfWork(u UnitOfWork) {
	if u != nil {
		s.uow = u
	}
}
func (s *ChatService) Send(ctx context.Context, p player.ID, ch chat.Channel, recipient player.ID, body string) (message chat.Message, err error) {
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		if ch == chat.ChannelAlliance {
			a, _, e := s.alliances.FindByPlayer(ctx, p)
			if e != nil {
				return apperror.New(apperror.Forbidden, "Канал союза доступен только его участникам")
			}
			if e = s.alliances.LockAlliance(ctx, a.ID); e != nil {
				return e
			}
		}
		var e error
		message, e = s.send(ctx, p, ch, recipient, body)
		return e
	})
	return
}

package memory

import (
	"context"
	"sort"

	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
	"real-city/backend/pkg/memorytx"
)

func (r *PlayerRepo) AdminPlayers(ctx context.Context, limit int) ([]player.Player, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := []player.Player{}
	for _, p := range r.players {
		if p.Status != player.StatusDeleted {
			items = append(items, p)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].ID < items[j].ID })
	if limit < 1 || limit > 100 {
		limit = 100
	}
	if len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}
func (r *SocialRepo) ListFlaggedMessages(ctx context.Context, limit int) ([]chat.Message, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := []chat.Message{}
	for _, m := range r.messages {
		if m.Flagged {
			items = append(items, m)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.Before(items[j].CreatedAt) })
	if limit < 1 || limit > 100 {
		limit = 100
	}
	if len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}
func (r *SocialRepo) ModerateMessage(ctx context.Context, a chat.ModerationAudit) error {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.Lock()
	defer r.mu.Unlock()
	for i, m := range r.messages {
		if m.ID == a.MessageID {
			m.Flagged = false
			if a.Action == "reject" {
				m.Body = "Сообщение удалено модератором"
			}
			r.messages[i] = m
			r.moderationAudit = append(r.moderationAudit, a)
			return nil
		}
	}
	return apperror.New(apperror.NotFound, "Сообщение не найдено")
}
func (r *SocialRepo) ListModerationAudit(ctx context.Context, limit int) ([]chat.ModerationAudit, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := append([]chat.ModerationAudit{}, r.moderationAudit...)
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.After(items[j].CreatedAt) })
	if limit < 1 || limit > 100 {
		limit = 100
	}
	if len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

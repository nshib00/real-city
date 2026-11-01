package service

import (
	"context"
	"fmt"
	"strings"
	"time"

	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type ModerationRepository interface {
	ListFlaggedMessages(context.Context, int) ([]chat.Message, error)
	ModerateMessage(context.Context, chat.ModerationAudit) error
	ListModerationAudit(context.Context, int) ([]chat.ModerationAudit, error)
}

type AdminService struct {
	players *PlayerService
	chat    *ChatService
}

func NewAdminService(players *PlayerService, ch *ChatService) *AdminService {
	return &AdminService{players, ch}
}
func (s *AdminService) Authorize(ctx context.Context, actor player.ID) error {
	if s.players == nil {
		return apperror.New(apperror.Forbidden, "Администрирование недоступно")
	}
	p, err := s.players.players.FindByID(ctx, actor)
	if err != nil {
		return err
	}
	if p.Status != player.StatusActive || p.Role != player.RoleAdmin {
		return apperror.New(apperror.Forbidden, "Требуется роль администратора")
	}
	return nil
}
func (s *AdminService) Players(ctx context.Context, actor player.ID, limit int) ([]player.Player, error) {
	if err := s.Authorize(ctx, actor); err != nil {
		return nil, err
	}
	repo, ok := s.players.players.(interface {
		AdminPlayers(context.Context, int) ([]player.Player, error)
	})
	if !ok {
		return nil, apperror.New(apperror.Conflict, "Список игроков недоступен")
	}
	return repo.AdminPlayers(ctx, limit)
}
func (s *AdminService) moderation() (ModerationRepository, error) {
	if s.chat == nil {
		return nil, apperror.New(apperror.Conflict, "Модерация недоступна")
	}
	repo, ok := s.chat.repo.(ModerationRepository)
	if !ok {
		return nil, apperror.New(apperror.Conflict, "Модерация недоступна")
	}
	return repo, nil
}
func (s *AdminService) Flagged(ctx context.Context, actor player.ID, limit int) ([]chat.Message, error) {
	if err := s.Authorize(ctx, actor); err != nil {
		return nil, err
	}
	repo, err := s.moderation()
	if err != nil {
		return nil, err
	}
	return repo.ListFlaggedMessages(ctx, limit)
}
func (s *AdminService) Audit(ctx context.Context, actor player.ID, limit int) ([]chat.ModerationAudit, error) {
	if err := s.Authorize(ctx, actor); err != nil {
		return nil, err
	}
	repo, err := s.moderation()
	if err != nil {
		return nil, err
	}
	return repo.ListModerationAudit(ctx, limit)
}
func (s *AdminService) Moderate(ctx context.Context, actor player.ID, id chat.MessageID, decision, reason string) error {
	if err := s.Authorize(ctx, actor); err != nil {
		return err
	}
	reason = strings.TrimSpace(reason)
	if (decision != "approve" && decision != "reject") || len([]rune(reason)) < 3 || len([]rune(reason)) > 500 {
		return apperror.New(apperror.Validation, "Укажите approve/reject и причину длиной 3–500 символов")
	}
	repo, err := s.moderation()
	if err != nil {
		return err
	}
	at := time.Now().UTC()
	audit := chat.ModerationAudit{ID: fmt.Sprintf("moderation_%s_%d", actor, at.UnixNano()), ActorID: actor, MessageID: id, Action: decision, Reason: reason, CreatedAt: at}
	err = transactional(ctx, s.chat.uow, func(ctx context.Context) error { return repo.ModerateMessage(ctx, audit) })
	if err == nil {
		s.chat.log.Info("admin.chat.moderated", "event", "admin.chat.moderated", "actor_id", actor, "message_id", id, "decision", decision, "audit_id", audit.ID)
	}
	return err
}

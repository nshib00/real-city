package service

import (
	"context"
	"errors"
	"fmt"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
	"strings"
	"time"
)

type AccountAdminRepository interface {
	ChangeAccount(context.Context, player.AccountAudit) error
	AccountAudit(context.Context, int) ([]player.AccountAudit, error)
}

func (s *AdminService) ChangeAccount(ctx context.Context, actor, target player.ID, status player.Status, role player.Role, reason string) error {
	if err := s.Authorize(ctx, actor); err != nil {
		return err
	}
	reason = strings.TrimSpace(reason)
	if target == "" || (status != player.StatusActive && status != player.StatusSuspended) || (role != player.RoleUser && role != player.RoleAdmin) || len([]rune(reason)) < 3 || len([]rune(reason)) > 500 {
		return apperror.New(apperror.Validation, "Укажите статус, роль и причину длиной 3–500 символов")
	}
	repo, ok := s.players.players.(AccountAdminRepository)
	if !ok {
		return apperror.New(apperror.Conflict, "Управление аккаунтами недоступно")
	}
	now := time.Now().UTC()
	audit := player.AccountAudit{ID: fmt.Sprintf("account_%s_%d", actor, now.UnixNano()), ActorID: actor, PlayerID: target, Status: status, Role: role, Reason: reason, CreatedAt: now}
	var uow UnitOfWork
	if s.chat != nil {
		uow = s.chat.uow
	}
	if _, ok := uow.(snapshotUnitOfWork); ok {
		uow = nil
	}
	if uow == nil {
		uow = snapshotUnitOfWork{[]any{s.players.players, s.players.sessions}}
	}
	err := transactional(ctx, uow, func(ctx context.Context) error {
		if err := repo.ChangeAccount(ctx, audit); err != nil {
			return err
		}
		return s.players.sessions.RevokePlayer(ctx, target)
	})
	if err == nil {
		s.players.log.Info("admin.account.changed", "actor_id", actor, "player_id", target, "status", status, "role", role, "audit_id", audit.ID)
	}
	return err
}

func (s *AdminService) AccountAudit(ctx context.Context, actor player.ID, limit int) ([]player.AccountAudit, error) {
	if err := s.Authorize(ctx, actor); err != nil {
		return nil, err
	}
	repo, ok := s.players.players.(AccountAdminRepository)
	if !ok {
		return nil, apperror.New(apperror.Conflict, "Аудит аккаунтов недоступен")
	}
	return repo.AccountAudit(ctx, limit)
}

// Called for each authenticated HTTP request and periodically for open WS.
func (s *PlayerService) ValidateAccess(ctx context.Context, id player.ID, session string) error {
	p, err := s.players.FindByID(ctx, id)
	if err != nil {
		var app *apperror.Error
		if errors.As(err, &app) && app.Kind == apperror.NotFound {
			return apperror.New(apperror.Unauthorized, "Аккаунт недоступен")
		}
		return apperror.Wrap(apperror.Internal, "Проверка сессии временно недоступна", err)
	}
	if p.Status != player.StatusActive {
		return apperror.New(apperror.Unauthorized, "Аккаунт недоступен")
	}
	store, ok := s.sessions.(interface {
		SessionActive(context.Context, player.ID, player.SessionID, time.Time) (bool, error)
	})
	if !ok {
		return apperror.New(apperror.Unauthorized, "Проверка сессии недоступна")
	}
	active, err := store.SessionActive(ctx, id, player.SessionID(session), time.Now().UTC())
	if err != nil {
		return err
	}
	if !active {
		return apperror.New(apperror.Unauthorized, "Сессия отозвана")
	}
	return nil
}

package service

import (
	"context"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
	"time"
)

type PvPProtectionRepository interface {
	PvPProtection(context.Context, player.ID, time.Time, int, int) (player.PvPState, int, error)
}

func (s *BuildingService) SetPvPProtection(repo PlayerRepository) {
	s.pvpProtection, _ = repo.(PvPProtectionRepository)
}

func (s *BuildingService) PvPDamage(ctx context.Context, target building.Building, attacker player.ID, damage int, now time.Time) (int, error) {
	if s.pvpProtection == nil || attacker == "" || target.OwnerID == "" || target.OwnerID == string(attacker) {
		return damage, nil
	}
	_, allowed, err := s.pvpProtection.PvPProtection(ctx, player.ID(target.OwnerID), now, damage, target.Health)
	return allowed, err
}

func (s *BuildingService) CheckPvPProtection(ctx context.Context, owner player.ID, now time.Time) error {
	if s.pvpProtection == nil {
		return nil
	}
	state, _, err := s.pvpProtection.PvPProtection(ctx, owner, now, 0, 0)
	if err != nil {
		return err
	}
	if !state.OfflineUntil.IsZero() {
		return apperror.New(apperror.Forbidden, "Постройка под временной офлайн-защитой")
	}
	if state.Damage >= player.PvPDailyDamage || state.Destructions >= player.PvPDailyDestructions {
		return apperror.New(apperror.Forbidden, "Владелец достиг суточного предела потерь PvP")
	}
	return nil
}

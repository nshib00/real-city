package service

import (
	"context"
	"log/slog"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/economy"
	"testing"
	"time"
)

func TestTreasuryPaymentsAndBuffsUseFullLedger(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewSocialRepo()
	eco := NewEconomyService(memory.NewEconomyRepo(), nil, slog.Default())
	svc := NewAllianceService(repo, eco, slog.Default())
	profile, err := svc.Create(ctx, "leader", "Союз испытаний")
	if err != nil {
		t.Fatal(err)
	}
	if err = repo.SaveMembership(ctx, alliance.Membership{AllianceID: profile.Alliance.ID, PlayerID: "member", Role: alliance.RoleMember, JoinedAt: time.Now()}); err != nil {
		t.Fatal(err)
	}
	grantTestResources(t, ctx, eco, "leader", economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 500})
	if _, err = svc.Donate(ctx, "leader", economy.ResourceWood, 500); err != nil {
		t.Fatal(err)
	}
	if _, err = svc.SpendTreasury(ctx, "member", "member", economy.ResourceWood, 1); err == nil {
		t.Fatal("member spent treasury")
	}
	if _, err = svc.UpgradeBuff(ctx, "leader", "build_speed"); err != nil {
		t.Fatal(err)
	}
	if percent, err := svc.Percent(ctx, "leader", "build_speed"); err != nil || percent != 3 {
		t.Fatal(percent, err)
	}
	if _, err = svc.SpendTreasury(ctx, "leader", "member", economy.ResourceWood, 100); err != nil {
		t.Fatal(err)
	}
	balance, _ := repo.TreasuryBalance(ctx, profile.Alliance.ID)
	if balance[economy.ResourceWood] != 375 {
		t.Fatal(balance)
	}
	if _, err = svc.SpendTreasury(ctx, "leader", "member", economy.ResourceWood, 376); err == nil {
		t.Fatal("overdraft accepted")
	}
	balance, _ = repo.TreasuryBalance(ctx, profile.Alliance.ID)
	if balance[economy.ResourceWood] != 375 {
		t.Fatal("failed withdrawal charged treasury")
	}
	member, _ := eco.Inventory(ctx, "member")
	if member.Items[economy.ResourceWood] != 100 {
		t.Fatal("recipient not credited")
	}
	builder := NewBuildingService(memory.NewBuildingRepo(), nil, slog.Default())
	builder.SetAllianceBenefits(svc)
	duration, err := builder.buffedDuration(ctx, "leader", time.Hour, "build_speed")
	if err != nil || duration != time.Hour*97/100 {
		t.Fatal(duration, err)
	}
	if err = repo.SaveBuff(ctx, alliance.Buff{AllianceID: profile.Alliance.ID, ID: "defense", Level: 999, UpdatedAt: time.Now()}); err != nil {
		t.Fatal(err)
	}
	damage, err := builder.ProtectedDamage(ctx, "leader", 100)
	if err != nil || damage != 90 {
		t.Fatal(damage, err)
	}
}

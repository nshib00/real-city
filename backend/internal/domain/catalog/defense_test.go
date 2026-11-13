package catalog

import (
	"testing"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
)

func TestDefenseFamiliesHaveCompleteLevelProgression(t *testing.T) {
	want := map[building.Type]int{
		building.TypeDefenseStakes:            6,
		building.TypeDefenseResinSnare:        4,
		building.TypeDefenseBoltThrower:       8,
		building.TypeDefenseStormCoil:         6,
		building.TypeDefenseAutomatonBay:      5,
		building.TypeDefenseGuardianEnclosure: 5,
	}
	for kind, count := range want {
		spec, ok := GetBuilding(kind)
		if !ok || len(spec.UpgradeLevels) != count {
			t.Fatalf("%s: incomplete catalog", kind)
		}
		for index, level := range spec.UpgradeLevels {
			if level.Level != index+1 || level.Health < 1 || level.Population < 1 || level.BuildDuration < time.Second || len(level.Cost) < 2 {
				t.Fatalf("%s level %d: invalid progression: %+v", kind, index+1, level)
			}
		}
	}
}

func TestDefenseEffectsMatchSpecifications(t *testing.T) {
	bolt, ok := DefenseWeaponLevel(building.TypeDefenseBoltThrower, 8)
	if !ok || bolt.Range != 4 || bolt.Damage != 25 || bolt.Cooldown != 2*time.Second || bolt.Ammo != "" || bolt.DamageType != "piercing" {
		t.Fatalf("bolt level 8: %+v", bolt)
	}
	storm, ok := DefenseWeaponLevel(building.TypeDefenseStormCoil, 6)
	if !ok || storm.Range != 4 || storm.Damage != 88 || storm.Cooldown != 20*time.Second || storm.Ammo != economy.ResourceFuel || storm.DamageType != "shock" {
		t.Fatalf("storm level 6: %+v", storm)
	}
	stakes, ok := DefenseTrapLevel(building.TypeDefenseStakes, 6)
	if !ok || stakes.Damage != 90 || stakes.MaxCharges != 3 || stakes.DamageType != "piercing" {
		t.Fatalf("stakes level 6: %+v", stakes)
	}
	resin, ok := DefenseTrapLevel(building.TypeDefenseResinSnare, 4)
	if !ok || resin.Damage != 36 || resin.MaxCharges != 2 || !resin.SlowsNextStep {
		t.Fatalf("resin level 4: %+v", resin)
	}
	for _, kind := range []building.Type{building.TypeDefenseAutomatonBay, building.TypeDefenseGuardianEnclosure} {
		base, ok := DefenseBaseLevel(kind, 5)
		if !ok || base.Slots != 6 || base.PatrolRadius != 5 {
			t.Fatalf("%s level 5: %+v", kind, base)
		}
	}
}

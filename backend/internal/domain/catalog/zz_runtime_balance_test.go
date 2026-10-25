package catalog

import (
	"bytes"
	"os"
	"testing"
)

func TestRuntimeBalanceSnapshot(t *testing.T) {
	raw, err := os.ReadFile("../../../../data/balance/v2.json")
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(raw, runtimeBalanceJSON) {
		t.Fatal("embedded balance differs from canonical data/balance/v2.json")
	}
	if _, err := decodeRuntimeBalance(raw); err != nil {
		t.Fatal(err)
	}
	if len(Resources) != 78 || len(monsterSpecs) != 8 || len(PlayerWeapons) != 9 {
		t.Fatalf("unexpected active balance: resources=%d monsters=%d weapons=%d", len(Resources), len(monsterSpecs), len(PlayerWeapons))
	}
	if RaidRules().RaidDamage <= 0 {
		t.Fatal("PvP balance was not loaded")
	}
}

func TestRuntimeBalanceRejectsInvalidVersion(t *testing.T) {
	corrupt := bytes.Replace(runtimeBalanceJSON, []byte(`"schema_version": 1`), []byte(`"schema_version": 99`), 1)
	if _, err := decodeRuntimeBalance(corrupt); err == nil {
		t.Fatal("invalid schema was accepted")
	}
}

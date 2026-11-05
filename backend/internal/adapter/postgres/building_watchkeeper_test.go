package postgres

import (
	"fmt"
	"testing"
)

type watchkeeperScanner struct{}

func (watchkeeperScanner) Scan(dest ...any) error {
	if len(dest) != 26 {
		return fmt.Errorf("building scan has %d columns, want 26", len(dest))
	}
	assigned, ok := dest[25].(*bool)
	if !ok {
		return fmt.Errorf("last building column is %T, want *bool", dest[25])
	}
	*assigned = true
	return nil
}

func TestScanBuildingWatchkeeper(t *testing.T) {
	item, err := scanBuilding(watchkeeperScanner{})
	if err != nil {
		t.Fatal(err)
	}
	if !item.TowerWatchkeeperAssigned {
		t.Fatal("watchkeeper assignment missing from scan")
	}
}

package handler

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"

	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

func TestBuildingListIncludesNearbyOtherPlayers(t *testing.T) {
	repo := memory.NewBuildingRepo()
	for _, item := range []building.Building{
		{ID: "own", MapID: service.DefaultWorldID, OwnerID: "p1", Tile: world.Coord{X: 3, Y: 4}},
		{ID: "foreign", MapID: service.DefaultWorldID, OwnerID: "p2", Tile: world.Coord{X: 34, Y: 4}},
		{ID: "distant", MapID: service.DefaultWorldID, OwnerID: "p2", Tile: world.Coord{X: 96, Y: 4}},
	} {
		if err := repo.Create(context.Background(), item); err != nil {
			t.Fatal(err)
		}
	}
	handler := NewBuildingHandler(service.NewBuildingService(repo, memory.NewWorldRepo(), slog.Default()))
	for _, test := range []struct {
		path string
		want []string
	}{
		{path: "/buildings", want: []string{"own"}},
		{path: "/buildings?scope=visible&x=0&y=0&radius=1", want: []string{"own", "foreign"}},
	} {
		request := httptest.NewRequest(http.MethodGet, test.path, nil)
		request = request.WithContext(middleware.WithPlayerID(request.Context(), player.ID("p1")))
		response := httptest.NewRecorder()
		handler.List(response, request)
		if response.Code != http.StatusOK {
			t.Fatalf("%s: status %d: %s", test.path, response.Code, response.Body.String())
		}
		var body struct {
			Buildings []struct {
				ID string `json:"id"`
			} `json:"buildings"`
		}
		if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil {
			t.Fatal(err)
		}
		if len(body.Buildings) != len(test.want) {
			t.Fatalf("%s: buildings = %#v", test.path, body.Buildings)
		}
		for index, id := range test.want {
			if body.Buildings[index].ID != id {
				t.Fatalf("%s: buildings = %#v", test.path, body.Buildings)
			}
		}
	}
}

type catalogResponseCost struct {
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
}

type catalogResponseLevel struct {
	Level        int                   `json:"level"`
	BuildSeconds int                   `json:"build_seconds"`
	Population   int                   `json:"population"`
	Health       int                   `json:"health"`
	Cost         []catalogResponseCost `json:"cost"`
	NextType     string                `json:"next_type"`
}

type catalogResponseBuilding struct {
	Type              string                 `json:"type"`
	Name              string                 `json:"name"`
	Category          string                 `json:"category"`
	Level             int                    `json:"level"`
	FootprintW        int                    `json:"footprint_w"`
	FootprintH        int                    `json:"footprint_h"`
	BuildSeconds      int                    `json:"build_seconds"`
	Population        int                    `json:"population"`
	Health            int                    `json:"health"`
	Cost              []catalogResponseCost  `json:"cost"`
	FirstLevel        bool                   `json:"first_level"`
	RequiresTownHall  bool                   `json:"requires_town_hall"`
	CountsTowardLimit bool                   `json:"counts_toward_limit"`
	UpgradeTo         []string               `json:"upgrade_to"`
	UpgradeLevels     []catalogResponseLevel `json:"upgrade_levels"`
}

func catalogCostsMatch(got []catalogResponseCost, want []building.Cost) bool {
	if len(got) != len(want) {
		return false
	}
	for index, expected := range want {
		if got[index].Resource != expected.Resource || got[index].Amount != expected.Amount {
			return false
		}
	}
	return true
}

func TestBuildingCatalogScopesReflectAvailabilityAndCompleteLevels(t *testing.T) {
	handler := NewBuildingHandler(service.NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.Default()))
	requestCatalog := func(path string) []catalogResponseBuilding {
		t.Helper()
		request := httptest.NewRequest(http.MethodGet, path, nil)
		response := httptest.NewRecorder()
		handler.Catalog(response, request)
		if response.Code != http.StatusOK {
			t.Fatalf("%s: status %d: %s", path, response.Code, response.Body.String())
		}
		var body struct {
			Buildings []catalogResponseBuilding `json:"buildings"`
		}
		if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil {
			t.Fatal(err)
		}
		return body.Buildings
	}

	all := requestCatalog("/api/v1/buildings/catalog?scope=all")
	wantAll := catalog.AllBuildings()
	if len(all) != len(wantAll) {
		t.Fatalf("scope=all returned %d types, want %d", len(all), len(wantAll))
	}
	allByID := make(map[string]catalogResponseBuilding, len(all))
	for _, item := range all {
		if _, duplicate := allByID[item.Type]; duplicate {
			t.Errorf("scope=all returned duplicate type %s", item.Type)
		}
		allByID[item.Type] = item
	}
	for _, want := range wantAll {
		got, ok := allByID[string(want.Type)]
		if !ok {
			t.Errorf("scope=all omitted %s", want.Type)
			continue
		}
		wantLevels := want.UpgradeLevels
		if len(wantLevels) == 0 {
			wantLevels = []catalog.BuildingUpgradeLevel{{
				Level: want.Level, BuildDuration: want.BuildDuration, Population: want.Population,
				Health: want.Health, Cost: want.Cost,
			}}
		}
		if got.Name != want.Name || got.Category != want.Category || got.Level != want.Level ||
			got.FootprintW != want.Footprint.Width || got.FootprintH != want.Footprint.Height ||
			got.BuildSeconds != int(want.BuildDuration.Seconds()) || got.Population != want.Population ||
			got.Health != want.Health || got.FirstLevel != catalog.CanPlaceDirectly(want.Type) ||
			got.RequiresTownHall != want.RequiresTownHall || got.CountsTowardLimit != want.CountsTowardLimit ||
			len(got.UpgradeLevels) != len(wantLevels) {
			t.Errorf("scope=all metadata differs from runtime catalog for %s: %#v", want.Type, got)
			continue
		}
		if !catalogCostsMatch(got.Cost, want.Cost) {
			t.Errorf("%s base cost does not match runtime catalog: %#v", want.Type, got.Cost)
		}
		for index, level := range wantLevels {
			if index >= len(got.UpgradeLevels) {
				break
			}
			actual := got.UpgradeLevels[index]
			if actual.Level != level.Level || actual.BuildSeconds != int(level.BuildDuration.Seconds()) ||
				actual.Population != level.Population || actual.Health != level.Health || actual.NextType != string(level.NextType) ||
				!catalogCostsMatch(actual.Cost, level.Cost) {
				t.Errorf("%s L%d does not match runtime catalog: %#v", want.Type, level.Level, actual)
			}
		}
	}

	direct := requestCatalog("/api/v1/buildings/catalog")
	wantDirect := catalog.FirstLevelBuildings()
	if len(direct) != len(wantDirect) {
		t.Fatalf("default scope returned %d types, want %d", len(direct), len(wantDirect))
	}
	wantIDs := make(map[string]bool, len(wantDirect))
	for _, item := range wantDirect {
		wantIDs[string(item.Type)] = true
	}
	for _, item := range direct {
		if !wantIDs[item.Type] || !item.FirstLevel {
			t.Errorf("default scope exposed non-placeable type %s", item.Type)
		}
	}
}

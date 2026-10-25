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

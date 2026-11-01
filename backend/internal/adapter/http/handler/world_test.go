package handler

import (
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

func TestViewportETagChangesWithTileVersion(t *testing.T) {
	repo := memory.NewWorldRepo()
	handler := NewWorldHandler(service.NewWorldService(repo, slog.Default()), nil)
	request := httptest.NewRequest(http.MethodGet, "/world/viewport?x=16&y=16&radius=1", nil)
	first := httptest.NewRecorder()
	handler.Viewport(first, request)
	if first.Code != http.StatusOK || first.Header().Get("ETag") == "" || first.Body.Len() == 0 {
		t.Fatalf("first response: code=%d etag=%q bytes=%d", first.Code, first.Header().Get("ETag"), first.Body.Len())
	}
	if len(handler.responseCache.items) != 1 {
		t.Fatalf("expected one cached JSON response, got %d", len(handler.responseCache.items))
	}
	repeated := httptest.NewRecorder()
	handler.Viewport(repeated, request)
	if repeated.Code != http.StatusOK || repeated.Body.String() != first.Body.String() || len(handler.responseCache.items) != 1 {
		t.Fatalf("repeated 200 did not reuse equivalent response: status=%d entries=%d", repeated.Code, len(handler.responseCache.items))
	}
	request.Header.Set("If-None-Match", first.Header().Get("ETag"))
	second := httptest.NewRecorder()
	handler.Viewport(second, request)
	if second.Code != http.StatusNotModified || second.Body.Len() != 0 {
		t.Fatalf("unchanged response: code=%d bytes=%d", second.Code, second.Body.Len())
	}
	chunk, _, err := repo.GetOrCreateChunk(request.Context(), service.DefaultWorldID, world.ChunkCoord{X: 0, Y: 0})
	if err != nil {
		t.Fatal(err)
	}
	tile := chunk.Tiles[0]
	tile.ForestDensity++
	if err := repo.UpdateTile(request.Context(), tile); err != nil {
		t.Fatal(err)
	}
	third := httptest.NewRecorder()
	handler.Viewport(third, request)
	if third.Code != http.StatusOK || third.Header().Get("ETag") == first.Header().Get("ETag") || third.Body.Len() == 0 {
		t.Fatalf("changed response: code=%d etag=%q bytes=%d", third.Code, third.Header().Get("ETag"), third.Body.Len())
	}
	if len(handler.responseCache.items) != 2 || third.Body.String() == first.Body.String() {
		t.Fatal("changed chunk reused stale JSON")
	}
}

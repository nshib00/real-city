package handler

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

func TestChunkVersionDiffOnlyReturnsChangedChunks(t *testing.T) {
	repo := memory.NewWorldRepo()
	handler := NewWorldHandler(service.NewWorldService(repo, slog.Default()), nil)
	request := httptest.NewRequest(http.MethodGet, "/world/chunks?x=0&y=0&radius=1", nil)
	first := httptest.NewRecorder()
	handler.Chunks(first, request)
	var snapshot struct {
		Chunks []struct {
			ChunkX  int   `json:"chunk_x"`
			ChunkY  int   `json:"chunk_y"`
			Version int64 `json:"version"`
		} `json:"chunks"`
	}
	if err := json.Unmarshal(first.Body.Bytes(), &snapshot); err != nil {
		t.Fatal(err)
	}
	if len(snapshot.Chunks) != 9 {
		t.Fatalf("initial chunk count = %d", len(snapshot.Chunks))
	}
	var known string
	for i, chunk := range snapshot.Chunks {
		if i > 0 {
			known += ","
		}
		known += fmt.Sprintf("%d:%d:%d", chunk.ChunkX, chunk.ChunkY, chunk.Version)
	}
	repeat := httptest.NewRecorder()
	handler.Chunks(repeat, httptest.NewRequest(http.MethodGet, "/world/chunks?x=0&y=0&radius=1&known="+known, nil))
	var diff struct {
		Chunks []json.RawMessage `json:"chunks"`
	}
	if err := json.Unmarshal(repeat.Body.Bytes(), &diff); err != nil {
		t.Fatal(err)
	}
	if repeat.Code != http.StatusOK || len(diff.Chunks) != 0 {
		t.Fatalf("unchanged diff status=%d chunks=%d", repeat.Code, len(diff.Chunks))
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
	changed := httptest.NewRecorder()
	handler.Chunks(changed, httptest.NewRequest(http.MethodGet, "/world/chunks?x=0&y=0&radius=1&known="+known, nil))
	if err := json.Unmarshal(changed.Body.Bytes(), &diff); err != nil {
		t.Fatal(err)
	}
	if changed.Code != http.StatusOK || len(diff.Chunks) != 1 {
		t.Fatalf("changed diff status=%d chunks=%d", changed.Code, len(diff.Chunks))
	}
	invalid := httptest.NewRecorder()
	handler.Chunks(invalid, httptest.NewRequest(http.MethodGet, "/world/chunks?x=0&y=0&radius=1&known=bad", nil))
	if invalid.Code != http.StatusBadRequest {
		t.Fatalf("invalid diff status=%d", invalid.Code)
	}
}

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

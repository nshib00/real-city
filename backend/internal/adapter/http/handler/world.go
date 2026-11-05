package handler

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"hash/fnv"
	"net/http"
	"strconv"
	"strings"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type WorldHandler struct {
	worlds        *service.WorldService
	forests       *service.ForestService
	responseCache *worldResponseCache
}

func NewWorldHandler(worlds *service.WorldService, forests *service.ForestService) *WorldHandler {
	return &WorldHandler{worlds: worlds, forests: forests, responseCache: newWorldResponseCache()}
}

func (h *WorldHandler) World(w http.ResponseWriter, r *http.Request) {
	worldMap, err := h.worlds.GetWorld(r.Context())
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, dto.WorldMap(worldMap))
}

func (h *WorldHandler) Chunks(w http.ResponseWriter, r *http.Request) {
	center, radius, err := parseChunkQuery(r)
	if err != nil {
		writeError(w, err)
		return
	}
	chunks, err := h.worlds.ListChunks(r.Context(), center, radius)
	if err != nil {
		writeError(w, err)
		return
	}
	h.writeChunks(w, r, chunks)
}

func (h *WorldHandler) Viewport(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query()
	x, err := parseInt(query.Get("x"), "x", 0)
	if err != nil {
		writeError(w, err)
		return
	}
	y, err := parseInt(query.Get("y"), "y", 0)
	if err != nil {
		writeError(w, err)
		return
	}
	radius, err := parseInt(query.Get("radius"), "radius", 48)
	if err != nil {
		writeError(w, err)
		return
	}
	chunks, err := h.worlds.LoadViewport(r.Context(), world.Viewport{Center: world.Coord{X: x, Y: y}, Radius: radius})
	if err != nil {
		writeError(w, err)
		return
	}
	h.writeChunks(w, r, chunks)
}

func (h *WorldHandler) writeChunks(w http.ResponseWriter, r *http.Request, chunks []world.Chunk) {
	known, err := parseKnownChunkVersions(r.URL.Query().Get("known"))
	if err != nil {
		writeError(w, err)
		return
	}
	if known != nil {
		changed := make([]world.Chunk, 0, len(chunks))
		for _, chunk := range chunks {
			version, exists := known[chunk.Coord]
			if !exists || version != chunk.Version {
				changed = append(changed, chunk)
			}
		}
		// A diff response depends on the client's versions and must not share the full-response ETag cache.
		w.Header().Set("Cache-Control", "private, no-store")
		writeJSON(w, http.StatusOK, envelope{"chunks": dto.Chunks(changed)})
		return
	}
	if writeNotModified(w, r, chunks) {
		return
	}
	key := w.Header().Get("ETag")
	data, ok := h.responseCache.get(key)
	if !ok {
		var err error
		data, err = json.Marshal(envelope{"chunks": dto.Chunks(chunks)})
		if err != nil {
			writeError(w, err)
			return
		}
		data = append(data, '\n')
		h.responseCache.put(key, data)
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(data)
}

func parseKnownChunkVersions(raw string) (map[world.ChunkCoord]int64, error) {
	if raw == "" {
		return nil, nil
	}
	parts := strings.Split(raw, ",")
	if len(parts) > 49 {
		return nil, apperror.New(apperror.Validation, "too many known chunk versions")
	}
	known := make(map[world.ChunkCoord]int64, len(parts))
	for _, part := range parts {
		values := strings.Split(part, ":")
		if len(values) != 3 {
			return nil, apperror.New(apperror.Validation, "invalid known chunk version")
		}
		x, xErr := strconv.Atoi(values[0])
		y, yErr := strconv.Atoi(values[1])
		version, versionErr := strconv.ParseInt(values[2], 10, 64)
		if xErr != nil || yErr != nil || versionErr != nil || x < 0 || y < 0 || x >= world.WorldChunks || y >= world.WorldChunks || version < 0 {
			return nil, apperror.New(apperror.Validation, "invalid known chunk version")
		}
		known[world.ChunkCoord{X: x, Y: y}] = version
	}
	return known, nil
}

func writeNotModified(w http.ResponseWriter, r *http.Request, chunks []world.Chunk) bool {
	hash := fnv.New64a()
	var data [24]byte
	for _, chunk := range chunks {
		binary.LittleEndian.PutUint64(data[0:8], uint64(chunk.Coord.X))
		binary.LittleEndian.PutUint64(data[8:16], uint64(chunk.Coord.Y))
		binary.LittleEndian.PutUint64(data[16:24], uint64(chunk.Version))
		_, _ = hash.Write(data[:])
	}
	etag := fmt.Sprintf("\"world-%016x\"", hash.Sum64())
	w.Header().Set("ETag", etag)
	w.Header().Set("Cache-Control", "private, no-cache")
	if r.Header.Get("If-None-Match") != etag {
		return false
	}
	w.WriteHeader(http.StatusNotModified)
	return true
}

func (h *WorldHandler) ChopForest(w http.ResponseWriter, r *http.Request) {
	playerID, ok := middleware.PlayerID(r.Context())
	if !ok {
		writeError(w, apperror.New(apperror.Unauthorized, "player id is missing"))
		return
	}
	var req dto.ChopForestRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	result, err := h.forests.Chop(r.Context(), playerID, world.Coord{X: req.TileX, Y: req.TileY})
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"tile": dto.Tile(result.Tile), "inventory": dto.Inventory(result.Inventory)})
}

func parseChunkQuery(r *http.Request) (world.ChunkCoord, int, error) {
	query := r.URL.Query()
	x, err := parseInt(query.Get("x"), "x", 0)
	if err != nil {
		return world.ChunkCoord{}, 0, err
	}
	y, err := parseInt(query.Get("y"), "y", 0)
	if err != nil {
		return world.ChunkCoord{}, 0, err
	}
	radius, err := parseInt(query.Get("radius"), "radius", service.DefaultChunkRadius)
	if err != nil {
		return world.ChunkCoord{}, 0, err
	}
	return world.ChunkCoord{X: x, Y: y}, radius, nil
}

func parseInt(raw string, field string, fallback int) (int, error) {
	if raw == "" {
		return fallback, nil
	}
	value, err := strconv.Atoi(raw)
	if err != nil {
		return 0, apperror.WithFields(apperror.Validation, "invalid query parameter", map[string]string{field: "must be an integer"})
	}
	return value, nil
}

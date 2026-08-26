-- +goose Up
CREATE TABLE IF NOT EXISTS world_maps (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    seed BIGINT NOT NULL,
    chunk_size INTEGER NOT NULL,
    spawn_radius INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS world_chunks (
    map_id TEXT NOT NULL REFERENCES world_maps(id) ON DELETE CASCADE,
    chunk_x INTEGER NOT NULL,
    chunk_y INTEGER NOT NULL,
    version BIGINT NOT NULL DEFAULT 1,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (map_id, chunk_x, chunk_y)
);

CREATE TABLE IF NOT EXISTS world_tiles (
    map_id TEXT NOT NULL REFERENCES world_maps(id) ON DELETE CASCADE,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    chunk_x INTEGER NOT NULL,
    chunk_y INTEGER NOT NULL,
    terrain TEXT NOT NULL,
    elevation INTEGER NOT NULL DEFAULT 0,
    safe_zone BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (map_id, tile_x, tile_y),
    FOREIGN KEY (map_id, chunk_x, chunk_y) REFERENCES world_chunks(map_id, chunk_x, chunk_y) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_world_chunks_coord ON world_chunks(map_id, chunk_x, chunk_y);
CREATE INDEX IF NOT EXISTS idx_world_chunks_version ON world_chunks(map_id, version);
CREATE INDEX IF NOT EXISTS idx_world_tiles_chunk ON world_tiles(map_id, chunk_x, chunk_y);
CREATE INDEX IF NOT EXISTS idx_world_tiles_coord ON world_tiles(map_id, tile_x, tile_y);
CREATE INDEX IF NOT EXISTS idx_world_tiles_terrain ON world_tiles(map_id, terrain);

-- +goose Down
DROP TABLE IF EXISTS world_tiles;
DROP TABLE IF EXISTS world_chunks;
DROP TABLE IF EXISTS world_maps;

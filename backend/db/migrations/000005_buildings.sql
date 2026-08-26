-- +goose Up
CREATE TABLE IF NOT EXISTS buildings (
    id TEXT PRIMARY KEY,
    map_id TEXT NOT NULL REFERENCES world_maps(id) ON DELETE CASCADE,
    owner_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    state TEXT NOT NULL,
    health INTEGER NOT NULL DEFAULT 100,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    footprint_w INTEGER NOT NULL DEFAULT 1,
    footprint_h INTEGER NOT NULL DEFAULT 1,
    started_at TIMESTAMPTZ NOT NULL,
    completes_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS building_jobs (
    id TEXT PRIMARY KEY,
    building_id TEXT NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    owner_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    state TEXT NOT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_buildings_owner ON buildings(owner_id);
CREATE INDEX IF NOT EXISTS idx_buildings_map_chunk ON buildings(map_id, tile_x, tile_y);
CREATE INDEX IF NOT EXISTS idx_buildings_type ON buildings(map_id, type);
CREATE INDEX IF NOT EXISTS idx_building_jobs_due ON building_jobs(state, due_at);

-- +goose Down
DROP TABLE IF EXISTS building_jobs;
DROP TABLE IF EXISTS buildings;

-- +goose Up
CREATE TABLE IF NOT EXISTS player_inventories (
    player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    resource TEXT NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (player_id, resource)
);

CREATE TABLE IF NOT EXISTS resource_nodes (
    id TEXT PRIMARY KEY,
    map_id TEXT NOT NULL REFERENCES world_maps(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    resource TEXT NOT NULL,
    amount INTEGER NOT NULL,
    max_amount INTEGER NOT NULL,
    state TEXT NOT NULL,
    owner_id TEXT REFERENCES players(id) ON DELETE SET NULL,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    respawn_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS production_jobs (
    id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    building_id TEXT NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    recipe_id TEXT NOT NULL,
    state TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completes_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS economy_transactions (
    id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    resource TEXT NOT NULL,
    amount INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_player_inventories_player ON player_inventories(player_id);
CREATE INDEX IF NOT EXISTS idx_resource_nodes_map_tile ON resource_nodes(map_id, tile_x, tile_y);
CREATE INDEX IF NOT EXISTS idx_resource_nodes_state_respawn ON resource_nodes(state, respawn_at);
CREATE INDEX IF NOT EXISTS idx_production_jobs_player_state ON production_jobs(player_id, state);
CREATE INDEX IF NOT EXISTS idx_production_jobs_due ON production_jobs(state, completes_at);
CREATE INDEX IF NOT EXISTS idx_economy_transactions_player ON economy_transactions(player_id, created_at DESC);

-- +goose Down
DROP TABLE IF EXISTS economy_transactions;
DROP TABLE IF EXISTS production_jobs;
DROP TABLE IF EXISTS resource_nodes;
DROP TABLE IF EXISTS player_inventories;


-- +goose Up
ALTER TABLE buildings
    ADD COLUMN IF NOT EXISTS field_stage INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS field_stage_started_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS field_stage_ready_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS field_super_crop BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE buildings
SET field_stage = 1,
    field_stage_started_at = COALESCE(field_stage_started_at, updated_at),
    field_stage_ready_at = COALESCE(field_stage_ready_at, updated_at + interval '34 seconds')
WHERE type = 'field_bed'
  AND state = 'active'
  AND field_stage = 0;

-- +goose Down
ALTER TABLE buildings
    DROP COLUMN IF EXISTS field_super_crop,
    DROP COLUMN IF EXISTS field_stage_ready_at,
    DROP COLUMN IF EXISTS field_stage_started_at,
    DROP COLUMN IF EXISTS field_stage;

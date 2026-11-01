-- +goose Up
ALTER TABLE player_xp_events ADD COLUMN requested_amount INTEGER;
UPDATE player_xp_events SET requested_amount=GREATEST(amount,1);
ALTER TABLE player_xp_events ALTER COLUMN requested_amount SET NOT NULL;
ALTER TABLE player_xp_events DROP CONSTRAINT player_xp_events_amount_check;
ALTER TABLE player_xp_events ADD CONSTRAINT player_xp_events_amount_check CHECK(amount>=0);
ALTER TABLE player_xp_events ADD CONSTRAINT player_xp_requested_positive CHECK(requested_amount>0);
CREATE INDEX player_xp_daily_policy ON player_xp_events(player_id,reason,created_at);
-- +goose Down
-- Zero awards are legitimate audit records; preserve them by keeping nonnegative amounts.
DROP INDEX player_xp_daily_policy;
ALTER TABLE player_xp_events DROP CONSTRAINT player_xp_requested_positive;
ALTER TABLE player_xp_events DROP COLUMN requested_amount;

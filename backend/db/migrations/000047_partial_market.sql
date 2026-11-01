-- +goose Up
ALTER TABLE market_orders ADD COLUMN filled_amount integer NOT NULL DEFAULT 0;
UPDATE market_orders SET filled_amount=amount WHERE status='filled';
ALTER TABLE market_orders ADD CONSTRAINT market_filled_amount CHECK(filled_amount>=0 AND filled_amount<=amount);
CREATE INDEX idx_market_open_resource ON market_orders(resource,side,created_at,id) WHERE status='open';
-- +goose Down
DROP INDEX idx_market_open_resource;
ALTER TABLE market_orders DROP COLUMN filled_amount;

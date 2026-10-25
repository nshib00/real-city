-- +goose Up
-- +goose StatementBegin
DO $$
BEGIN
    IF (SELECT version FROM game_balance_version WHERE singleton = true) <> 1 THEN
        RAISE EXCEPTION 'building balance v2 requires world balance v1';
    END IF;
END $$;
-- +goose StatementEnd

-- Сохраняем долю HP у уже построенных домов при переходе на новый максимум.
UPDATE buildings
SET health = CASE WHEN health <= 0 THEN 0 ELSE GREATEST(1, ROUND(health::numeric * 15500 / 100)::integer) END
WHERE type = 'villa' AND level = 4;

UPDATE buildings
SET health = CASE WHEN health <= 0 THEN 0 ELSE GREATEST(1, ROUND(health::numeric * 10000 / 100)::integer) END,
    level = 1
WHERE type = 'apartment_house' AND level = 4;

UPDATE game_balance_version SET version = 2, applied_at = now() WHERE singleton = true;

-- +goose Down
-- После появления построек новых уровней автоматический откат потеряет данные.
-- +goose StatementBegin
DO $$ BEGIN
    RAISE EXCEPTION 'balance v2 downgrade requires a backup of the v1 world';
END $$;
-- +goose StatementEnd

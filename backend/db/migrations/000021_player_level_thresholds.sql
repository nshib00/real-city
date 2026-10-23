-- +goose Up
UPDATE player_profiles
SET level = CASE
    WHEN xp >= 18121200 THEN 15
    WHEN xp >= 8121200 THEN 14
    WHEN xp >= 3621200 THEN 13
    WHEN xp >= 1621200 THEN 12
    WHEN xp >= 721200 THEN 11
    WHEN xp >= 321200 THEN 10
    WHEN xp >= 141200 THEN 9
    WHEN xp >= 61200 THEN 8
    WHEN xp >= 26200 THEN 7
    WHEN xp >= 11200 THEN 6
    WHEN xp >= 4700 THEN 5
    WHEN xp >= 1900 THEN 4
    WHEN xp >= 700 THEN 3
    WHEN xp >= 200 THEN 2
    ELSE 1
END;

-- +goose Down
UPDATE player_profiles
SET level = CASE
    WHEN xp >= 17400 THEN 15
    WHEN xp >= 14200 THEN 14
    WHEN xp >= 11500 THEN 13
    WHEN xp >= 9200 THEN 12
    WHEN xp >= 7200 THEN 11
    WHEN xp >= 5500 THEN 10
    WHEN xp >= 4100 THEN 9
    WHEN xp >= 3000 THEN 8
    WHEN xp >= 2100 THEN 7
    WHEN xp >= 1400 THEN 6
    WHEN xp >= 900 THEN 5
    WHEN xp >= 500 THEN 4
    WHEN xp >= 250 THEN 3
    WHEN xp >= 100 THEN 2
    ELSE 1
END;

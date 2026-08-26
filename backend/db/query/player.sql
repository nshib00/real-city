-- name: CreatePlayer
INSERT INTO players (id, email, name, password_hash, status, role, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $7);

-- name: CreateProfile
INSERT INTO player_profiles (
    player_id,
    display_name,
    avatar_url,
    raid_alerts,
    production_ready,
    market_updates,
    render_quality,
    updated_at
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8);

-- name: FindPlayerByID
SELECT
    p.id,
    p.email,
    p.name,
    p.password_hash,
    p.status,
    p.role,
    p.created_at,
    p.updated_at,
    pr.display_name,
    pr.avatar_url,
    pr.raid_alerts,
    pr.production_ready,
    pr.market_updates,
    pr.render_quality,
    pr.updated_at
FROM players p
JOIN player_profiles pr ON pr.player_id = p.id
WHERE p.id = $1 AND p.status <> 'deleted';

-- name: FindPlayerByEmail
SELECT
    p.id,
    p.email,
    p.name,
    p.password_hash,
    p.status,
    p.role,
    p.created_at,
    p.updated_at,
    pr.display_name,
    pr.avatar_url,
    pr.raid_alerts,
    pr.production_ready,
    pr.market_updates,
    pr.render_quality,
    pr.updated_at
FROM players p
JOIN player_profiles pr ON pr.player_id = p.id
WHERE p.email = $1 AND p.status <> 'deleted';

-- name: UpdateProfile
UPDATE player_profiles
SET
    display_name = $2,
    avatar_url = $3,
    raid_alerts = $4,
    production_ready = $5,
    market_updates = $6,
    render_quality = $7,
    updated_at = $8
WHERE player_id = $1;

-- name: UpdatePassword
UPDATE players SET password_hash = $2, updated_at = $3 WHERE id = $1 AND status <> 'deleted';

-- name: DeletePlayer
UPDATE players SET status = 'deleted', updated_at = $2 WHERE id = $1;

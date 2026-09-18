-- name: CreateAlliance :exec
INSERT INTO alliances (id, name, description, leader_id, level, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7);

-- name: GetAlliance :one
SELECT id, name, description, leader_id, level, created_at, updated_at
FROM alliances
WHERE id = $1;

-- name: GetAllianceByPlayer :one
SELECT a.id, a.name, a.description, a.leader_id, a.level, a.created_at, a.updated_at,
       m.player_id, m.role, m.treasurer, m.joined_at
FROM alliances a
JOIN alliance_members m ON m.alliance_id = a.id
WHERE m.player_id = $1;

-- name: ListAllianceMembers :many
SELECT alliance_id, player_id, role, treasurer, joined_at
FROM alliance_members
WHERE alliance_id = $1
ORDER BY joined_at ASC;

-- name: UpsertAllianceMember :exec
INSERT INTO alliance_members (alliance_id, player_id, role, treasurer, joined_at)
VALUES ($1, $2, $3, $4, $5)
ON CONFLICT (alliance_id, player_id)
DO UPDATE SET role = EXCLUDED.role, treasurer = EXCLUDED.treasurer;

-- name: DeleteAllianceMember :exec
DELETE FROM alliance_members
WHERE alliance_id = $1 AND player_id = $2;

-- name: CreateAllianceInvite :exec
INSERT INTO alliance_invites (id, alliance_id, inviter_id, invitee_id, status, created_at, responded_at)
VALUES ($1, $2, $3, $4, $5, $6, $7);

-- name: GetAllianceInvite :one
SELECT id, alliance_id, inviter_id, invitee_id, status, created_at, responded_at
FROM alliance_invites
WHERE id = $1;

-- name: ListPlayerAllianceInvites :many
SELECT id, alliance_id, inviter_id, invitee_id, status, created_at, responded_at
FROM alliance_invites
WHERE invitee_id = $1 AND status = 'pending'
ORDER BY created_at DESC;

-- name: UpdateAllianceInvite :exec
UPDATE alliance_invites
SET status = $2, responded_at = $3
WHERE id = $1;

-- name: AddAllianceTreasuryEntry :exec
INSERT INTO alliance_treasury (id, alliance_id, player_id, kind, resource, amount, description, created_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8);

-- name: ListAllianceTreasury :many
SELECT id, alliance_id, player_id, kind, resource, amount, description, created_at
FROM alliance_treasury
WHERE alliance_id = $1
ORDER BY created_at DESC
LIMIT $2;

-- name: UpsertAllianceBuff :exec
INSERT INTO alliance_buffs (alliance_id, id, level, updated_at)
VALUES ($1, $2, $3, $4)
ON CONFLICT (alliance_id, id)
DO UPDATE SET level = EXCLUDED.level, updated_at = EXCLUDED.updated_at;

-- name: ListAllianceBuffs :many
SELECT alliance_id, id, level, updated_at
FROM alliance_buffs
WHERE alliance_id = $1
ORDER BY id ASC;

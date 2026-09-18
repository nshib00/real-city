-- name: AddChatMessage :exec
INSERT INTO chat_messages (id, channel, author_id, alliance_id, recipient_id, body, flagged, created_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8);

-- name: ListChatMessages :many
SELECT id, channel, author_id, alliance_id, recipient_id, body, flagged, created_at
FROM chat_messages
WHERE channel = $1
  AND ($2::text = '' OR alliance_id = $2)
  AND ($3::text = '' OR author_id = $3 OR recipient_id = $3)
ORDER BY created_at DESC
LIMIT $4;

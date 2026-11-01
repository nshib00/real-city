package postgres

import (
	"context"

	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

func (r *PlayerRepo) AdminPlayers(ctx context.Context, limit int) ([]player.Player, error) {
	if limit < 1 || limit > 100 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT id FROM players WHERE status<>'deleted' ORDER BY id LIMIT $1`, limit)
	if err != nil {
		return nil, err
	}
	ids := []player.ID{}
	for rows.Next() {
		var id player.ID
		if err := rows.Scan(&id); err != nil {
			rows.Close()
			return nil, err
		}
		ids = append(ids, id)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	items := []player.Player{}
	for _, id := range ids {
		p, err := r.FindByID(ctx, id)
		if err != nil {
			return nil, err
		}
		items = append(items, p)
	}
	return items, nil
}
func (r *SocialRepo) ListFlaggedMessages(ctx context.Context, limit int) ([]chat.Message, error) {
	if limit < 1 || limit > 100 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT id,channel,author_id,COALESCE(alliance_id,''),COALESCE(recipient_id,''),body,flagged,created_at FROM chat_messages WHERE flagged ORDER BY created_at,id LIMIT $1`, limit)
	return collectSocial(rows, err, func(row socialScanner) (m chat.Message, err error) {
		err = row.Scan(&m.ID, &m.Channel, &m.AuthorID, &m.AllianceID, &m.Recipient, &m.Body, &m.Flagged, &m.CreatedAt)
		return
	})
}
func (r *SocialRepo) ModerateMessage(ctx context.Context, a chat.ModerationAudit) error {
	result, err := execer(ctx, r.db).ExecContext(ctx, `UPDATE chat_messages SET flagged=false,body=CASE WHEN $2='reject' THEN 'Сообщение удалено модератором' ELSE body END WHERE id=$1`, a.MessageID, a.Action)
	if err != nil {
		return err
	}
	count, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if count != 1 {
		return apperror.New(apperror.NotFound, "Сообщение не найдено")
	}
	_, err = execer(ctx, r.db).ExecContext(ctx, `INSERT INTO chat_moderation_audit(id,actor_id,message_id,action,reason,created_at) VALUES($1,$2,$3,$4,$5,$6)`, a.ID, a.ActorID, a.MessageID, a.Action, a.Reason, a.CreatedAt)
	return err
}
func (r *SocialRepo) ListModerationAudit(ctx context.Context, limit int) ([]chat.ModerationAudit, error) {
	if limit < 1 || limit > 100 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT id,actor_id,message_id,action,reason,created_at FROM chat_moderation_audit ORDER BY created_at DESC,id DESC LIMIT $1`, limit)
	return collectSocial(rows, err, func(row socialScanner) (a chat.ModerationAudit, err error) {
		err = row.Scan(&a.ID, &a.ActorID, &a.MessageID, &a.Action, &a.Reason, &a.CreatedAt)
		return
	})
}

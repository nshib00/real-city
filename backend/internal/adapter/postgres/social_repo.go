package postgres

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type SocialRepo struct{ db *sql.DB }

func NewSocialRepo(db *sql.DB) *SocialRepo { return &SocialRepo{db: db} }
func socialError(err error) error {
	if errors.Is(err, sql.ErrNoRows) {
		return apperror.New(apperror.NotFound, "social object not found")
	}
	return err
}

type socialScanner interface{ Scan(...any) error }

func scanAlliance(row socialScanner) (a alliance.Alliance, err error) {
	err = socialError(row.Scan(&a.ID, &a.Name, &a.Description, &a.LeaderID, &a.Level, &a.CreatedAt, &a.UpdatedAt))
	return
}
func scanMember(row socialScanner) (a alliance.Membership, err error) {
	err = row.Scan(&a.AllianceID, &a.PlayerID, &a.Role, &a.Treasurer, &a.JoinedAt)
	return
}
func scanInvite(row socialScanner) (a alliance.Invite, err error) {
	err = socialError(row.Scan(&a.ID, &a.AllianceID, &a.InviterID, &a.InviteeID, &a.Status, &a.CreatedAt, &a.RespondedAt))
	return
}
func scanOrder(row socialScanner) (a market.Order, err error) {
	err = socialError(row.Scan(&a.ID, &a.PlayerID, &a.Side, &a.Resource, &a.Amount, &a.Price, &a.Fee, &a.Status, &a.CreatedAt, &a.UpdatedAt, &a.FilledAmount))
	return
}
func collectSocial[T any](rows *sql.Rows, err error, scan func(socialScanner) (T, error)) ([]T, error) {
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]T, 0)
	for rows.Next() {
		a, e := scan(rows)
		if e != nil {
			return nil, e
		}
		items = append(items, a)
	}
	return items, rows.Err()
}
func (r *SocialRepo) Create(ctx context.Context, a alliance.Alliance) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `INSERT INTO alliances(id,name,description,leader_id,level,created_at,updated_at) VALUES($1,$2,$3,$4,$5,$6,$7)`, a.ID, a.Name, a.Description, a.LeaderID, a.Level, a.CreatedAt, a.UpdatedAt)
	return err
}
func (r *SocialRepo) FindByID(ctx context.Context, id alliance.ID) (alliance.Alliance, error) {
	return scanAlliance(execer(ctx, r.db).QueryRowContext(ctx, `SELECT id,name,description,leader_id,level,created_at,updated_at FROM alliances WHERE id=$1`, id))
}
func (r *SocialRepo) FindByPlayer(ctx context.Context, id player.ID) (alliance.Alliance, alliance.Membership, error) {
	m, err := scanMember(execer(ctx, r.db).QueryRowContext(ctx, `SELECT alliance_id,player_id,role,treasurer,joined_at FROM alliance_members WHERE player_id=$1`, id))
	if err != nil {
		return alliance.Alliance{}, m, socialError(err)
	}
	a, err := r.FindByID(ctx, m.AllianceID)
	return a, m, err
}
func (r *SocialRepo) ListMembers(ctx context.Context, id alliance.ID) ([]alliance.Membership, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT alliance_id,player_id,role,treasurer,joined_at FROM alliance_members WHERE alliance_id=$1 ORDER BY joined_at,player_id`, id)
	return collectSocial(rows, err, scanMember)
}
func (r *SocialRepo) SaveMembership(ctx context.Context, a alliance.Membership) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `INSERT INTO alliance_members(alliance_id,player_id,role,treasurer,joined_at) VALUES($1,$2,$3,$4,$5) ON CONFLICT(alliance_id,player_id) DO UPDATE SET role=EXCLUDED.role,treasurer=EXCLUDED.treasurer`, a.AllianceID, a.PlayerID, a.Role, a.Treasurer, a.JoinedAt)
	return err
}
func (r *SocialRepo) DeleteMembership(ctx context.Context, id alliance.ID, p player.ID) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `DELETE FROM alliance_members WHERE alliance_id=$1 AND player_id=$2`, id, p)
	return err
}
func (r *SocialRepo) DeleteAlliance(ctx context.Context, id alliance.ID) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `DELETE FROM alliances WHERE id=$1`, id)
	return err
}
func (r *SocialRepo) LockAlliance(ctx context.Context, id alliance.ID) error {
	var key string
	return socialError(execer(ctx, r.db).QueryRowContext(ctx, `SELECT id FROM alliances WHERE id=$1 FOR UPDATE`, id).Scan(&key))
}
func (r *SocialRepo) CreateInvite(ctx context.Context, a alliance.Invite) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `INSERT INTO alliance_invites(id,alliance_id,inviter_id,invitee_id,status,created_at,responded_at) VALUES($1,$2,$3,$4,$5,$6,$7)`, a.ID, a.AllianceID, a.InviterID, a.InviteeID, a.Status, a.CreatedAt, a.RespondedAt)
	return err
}
func (r *SocialRepo) FindInvite(ctx context.Context, id alliance.InviteID) (alliance.Invite, error) {
	return scanInvite(execer(ctx, r.db).QueryRowContext(ctx, `SELECT id,alliance_id,inviter_id,invitee_id,status,created_at,responded_at FROM alliance_invites WHERE id=$1`, id))
}
func (r *SocialRepo) ListInvitesForPlayer(ctx context.Context, id player.ID) ([]alliance.Invite, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT id,alliance_id,inviter_id,invitee_id,status,created_at,responded_at FROM alliance_invites WHERE invitee_id=$1 AND status='pending' ORDER BY created_at DESC,id`, id)
	return collectSocial(rows, err, scanInvite)
}
func (r *SocialRepo) UpdateInvite(ctx context.Context, a alliance.Invite) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `UPDATE alliance_invites SET status=$2,responded_at=$3 WHERE id=$1`, a.ID, a.Status, a.RespondedAt)
	return err
}
func (r *SocialRepo) AddTreasuryEntry(ctx context.Context, a alliance.TreasuryEntry) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `INSERT INTO alliance_treasury(id,alliance_id,player_id,kind,resource,amount,description,created_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8)`, a.ID, a.AllianceID, a.PlayerID, a.Kind, a.Resource, a.Amount, a.Description, a.CreatedAt)
	return err
}
func (r *SocialRepo) ListTreasury(ctx context.Context, id alliance.ID, limit int) ([]alliance.TreasuryEntry, error) {
	if limit <= 0 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT id,alliance_id,player_id,kind,resource,amount,description,created_at FROM alliance_treasury WHERE alliance_id=$1 ORDER BY created_at DESC,id LIMIT $2`, id, limit)
	return collectSocial(rows, err, func(row socialScanner) (a alliance.TreasuryEntry, e error) {
		e = row.Scan(&a.ID, &a.AllianceID, &a.PlayerID, &a.Kind, &a.Resource, &a.Amount, &a.Description, &a.CreatedAt)
		return
	})
}
func (r *SocialRepo) SaveBuff(ctx context.Context, a alliance.Buff) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `INSERT INTO alliance_buffs(alliance_id,id,level,updated_at) VALUES($1,$2,$3,$4) ON CONFLICT(alliance_id,id) DO UPDATE SET level=EXCLUDED.level,updated_at=EXCLUDED.updated_at`, a.AllianceID, a.ID, a.Level, a.UpdatedAt)
	return err
}
func (r *SocialRepo) ListBuffs(ctx context.Context, id alliance.ID) ([]alliance.Buff, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT alliance_id,id,level,updated_at FROM alliance_buffs WHERE alliance_id=$1 ORDER BY id`, id)
	return collectSocial(rows, err, func(row socialScanner) (a alliance.Buff, e error) {
		e = row.Scan(&a.AllianceID, &a.ID, &a.Level, &a.UpdatedAt)
		return
	})
}
func (r *SocialRepo) AddTerritoryAid(ctx context.Context, a alliance.TerritoryAid) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `INSERT INTO alliance_territory_aid(alliance_id,target_type,target_id,player_id,created_at) VALUES($1,$2,$3,$4,$5)`, a.AllianceID, a.TargetType, a.TargetID, a.PlayerID, a.CreatedAt)
	return err
}
func (r *SocialRepo) ListTerritoryAid(ctx context.Context, id alliance.ID) ([]alliance.TerritoryAid, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT alliance_id,target_type,target_id,player_id,created_at FROM alliance_territory_aid WHERE alliance_id=$1 ORDER BY created_at`, id)
	return collectSocial(rows, err, func(row socialScanner) (a alliance.TerritoryAid, e error) {
		e = row.Scan(&a.AllianceID, &a.TargetType, &a.TargetID, &a.PlayerID, &a.CreatedAt)
		return
	})
}
func (r *SocialRepo) AddMessage(ctx context.Context, a chat.Message) error {
	audience, err := json.Marshal(a.Audience)
	if err != nil {
		return err
	}
	if a.Audience == nil {
		audience = []byte(`[]`)
	}
	_, err = execer(ctx, r.db).ExecContext(ctx, `INSERT INTO chat_messages(id,channel,author_id,alliance_id,recipient_id,body,flagged,created_at,audience) VALUES($1,$2,$3,NULLIF($4,''),NULLIF($5,''),$6,$7,$8,$9)`, a.ID, a.Channel, a.AuthorID, a.AllianceID, a.Recipient, a.Body, a.Flagged, a.CreatedAt, audience)
	return err
}
func (r *SocialRepo) ListMessages(ctx context.Context, p player.ID, ch chat.Channel, id alliance.ID, limit int, before ...chat.Cursor) ([]chat.Message, error) {
	if limit <= 0 || limit > 100 {
		limit = 100
	}
	var cursor chat.Cursor
	if len(before) > 0 {
		cursor = before[0]
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT id,channel,author_id,COALESCE(alliance_id,''),COALESCE(recipient_id,''),body,flagged,created_at FROM chat_messages WHERE channel=$1 AND ($1<>'alliance' OR alliance_id=$2) AND ($1<>'private' OR author_id=$3 OR recipient_id=$3) AND ($1<>'nearby' OR audience ? $3::text) AND ($5='' OR (created_at,id)<($6::timestamptz,$5::text)) ORDER BY created_at DESC,id DESC LIMIT $4`, ch, id, p, limit, cursor.ID, cursor.CreatedAt)
	return collectSocial(rows, err, func(row socialScanner) (a chat.Message, e error) {
		e = row.Scan(&a.ID, &a.Channel, &a.AuthorID, &a.AllianceID, &a.Recipient, &a.Body, &a.Flagged, &a.CreatedAt)
		return
	})
}
func (r *SocialRepo) CreateOrder(ctx context.Context, a market.Order) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `INSERT INTO market_orders(id,player_id,side,resource,amount,price,fee,status,created_at,updated_at,filled_amount) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)`, a.ID, a.PlayerID, a.Side, a.Resource, a.Amount, a.Price, a.Fee, a.Status, a.CreatedAt, a.UpdatedAt, a.FilledAmount)
	return err
}
func (r *SocialRepo) FindOrder(ctx context.Context, id market.OrderID) (market.Order, error) {
	return scanOrder(execer(ctx, r.db).QueryRowContext(ctx, `SELECT id,player_id,side,resource,amount,price,fee,status,created_at,updated_at,filled_amount FROM market_orders WHERE id=$1`, id))
}
func (r *SocialRepo) UpdateOrder(ctx context.Context, a market.Order) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `UPDATE market_orders SET status=$2,updated_at=$3,filled_amount=$4 WHERE id=$1`, a.ID, a.Status, a.UpdatedAt, a.FilledAmount)
	return err
}
func (r *SocialRepo) ListOrders(ctx context.Context, status market.Status, limit int) ([]market.Order, error) {
	if limit <= 0 || limit > 100 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT id,player_id,side,resource,amount,price,fee,status,created_at,updated_at,filled_amount FROM market_orders WHERE ($1='' OR status=$1) ORDER BY created_at DESC,id LIMIT $2`, status, limit)
	return collectSocial(rows, err, scanOrder)
}

func (r *SocialRepo) ReadAt(ctx context.Context, p player.ID, scope string) (at time.Time, err error) {
	err = execer(ctx, r.db).QueryRowContext(ctx, `SELECT read_at FROM chat_reads WHERE player_id=$1 AND scope=$2`, p, scope).Scan(&at)
	if errors.Is(err, sql.ErrNoRows) {
		return time.Time{}, nil
	}
	return
}
func (r *SocialRepo) SaveReadAt(ctx context.Context, p player.ID, scope string, at time.Time) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `INSERT INTO chat_reads(player_id,scope,read_at) VALUES($1,$2,$3) ON CONFLICT(player_id,scope) DO UPDATE SET read_at=GREATEST(chat_reads.read_at,EXCLUDED.read_at)`, p, scope, at)
	return err
}
func (r *SocialRepo) CountUnread(ctx context.Context, p player.ID, ch chat.Channel, id alliance.ID, after time.Time) (count int, err error) {
	err = execer(ctx, r.db).QueryRowContext(ctx, `SELECT count(*) FROM chat_messages WHERE channel=$1 AND ($1<>'alliance' OR alliance_id=$2) AND ($1<>'private' OR recipient_id=$3) AND ($1<>'nearby' OR audience ? $3::text) AND author_id<>$3 AND NOT flagged AND created_at>$4`, ch, id, p, after).Scan(&count)
	return
}

func (r *SocialRepo) UpdateLeader(ctx context.Context, id alliance.ID, p player.ID) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `UPDATE alliances SET leader_id=$2,updated_at=now() WHERE id=$1`, id, p)
	return err
}

func (r *SocialRepo) LockMarket(ctx context.Context, resource economy.ResourceType) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `SELECT pg_advisory_xact_lock(hashtextextended($1,0))`, "market:trades")
	return err
}
func (r *SocialRepo) FindMatch(ctx context.Context, item market.Order) (market.Order, error) {
	return scanOrder(execer(ctx, r.db).QueryRowContext(ctx, `SELECT id,player_id,side,resource,amount,price,fee,status,created_at,updated_at,filled_amount FROM market_orders WHERE status='open' AND side<>$1 AND resource=$2 AND player_id<>$4 AND amount>filled_amount AND (($1='buy' AND price::bigint*$3<= $5::bigint*amount) OR ($1='sell' AND price::bigint*$3>= $5::bigint*amount)) AND LEAST((amount-filled_amount)::bigint,$3::bigint-$6::bigint)>=lcm(amount::bigint/gcd(amount::bigint,price::bigint),$3::bigint/gcd($3::bigint,$5::bigint)) ORDER BY CASE WHEN $1='buy' THEN price::numeric/amount ELSE -price::numeric/amount END,created_at,id LIMIT 1 FOR UPDATE`, item.Side, item.Resource, item.Amount, item.PlayerID, item.Price, item.FilledAmount))
}
func (r *SocialRepo) TreasuryBalance(ctx context.Context, id alliance.ID) (map[economy.ResourceType]int, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT resource,sum(CASE WHEN kind='donation' THEN amount ELSE -amount END) FROM alliance_treasury WHERE alliance_id=$1 GROUP BY resource`, id)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	balance := map[economy.ResourceType]int{}
	for rows.Next() {
		var resource economy.ResourceType
		var amount int
		if err = rows.Scan(&resource, &amount); err != nil {
			return nil, err
		}
		balance[resource] = amount
	}
	return balance, rows.Err()
}

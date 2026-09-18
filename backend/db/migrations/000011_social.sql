-- +goose Up
CREATE TABLE IF NOT EXISTS alliances (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL DEFAULT '',
  leader_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  level INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alliance_members (
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('leader', 'deputy', 'officer', 'member')),
  treasurer BOOLEAN NOT NULL DEFAULT false,
  joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (alliance_id, player_id),
  UNIQUE (player_id)
);

CREATE TABLE IF NOT EXISTS alliance_invites (
  id TEXT PRIMARY KEY,
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  inviter_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  invitee_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'declined')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  responded_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS alliance_treasury (
  id TEXT PRIMARY KEY,
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('donation', 'spend')),
  resource TEXT NOT NULL,
  amount INTEGER NOT NULL CHECK (amount > 0),
  description TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alliance_buffs (
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  id TEXT NOT NULL,
  level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (alliance_id, id)
);

CREATE TABLE IF NOT EXISTS alliance_territory_aid (
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id TEXT PRIMARY KEY,
  channel TEXT NOT NULL CHECK (channel IN ('global', 'nearby', 'alliance', 'private')),
  author_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  alliance_id TEXT REFERENCES alliances(id) ON DELETE CASCADE,
  recipient_id TEXT REFERENCES players(id) ON DELETE CASCADE,
  body TEXT NOT NULL,
  flagged BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS market_orders (
  id TEXT PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
  resource TEXT NOT NULL,
  amount INTEGER NOT NULL CHECK (amount > 0),
  price INTEGER NOT NULL CHECK (price > 0),
  fee INTEGER NOT NULL CHECK (fee > 0),
  status TEXT NOT NULL CHECK (status IN ('open', 'filled', 'cancelled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alliance_invites_invitee_status ON alliance_invites(invitee_id, status);
CREATE INDEX IF NOT EXISTS idx_chat_messages_channel_created ON chat_messages(channel, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_orders_status_created ON market_orders(status, created_at DESC);

-- +goose Down
DROP TABLE IF EXISTS market_orders;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS alliance_territory_aid;
DROP TABLE IF EXISTS alliance_buffs;
DROP TABLE IF EXISTS alliance_treasury;
DROP TABLE IF EXISTS alliance_invites;
DROP TABLE IF EXISTS alliance_members;
DROP TABLE IF EXISTS alliances;

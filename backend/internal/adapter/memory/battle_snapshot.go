package memory

import (
	"maps"

	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
)

// Snapshots are taken under the shared memory transaction gate.
func (r *PlayerRepo) Snapshot() func() {
	r.mu.RLock()
	players, emails, names := maps.Clone(r.players), maps.Clone(r.emailID), maps.Clone(r.nameID)
	events, presence := maps.Clone(r.xpEvents), maps.Clone(r.presence)
	audit := maps.Clone(r.xpAudit)
	accounts := append([]player.AccountAudit(nil), r.accountAudit...)
	pvp := maps.Clone(r.pvp)
	r.mu.RUnlock()
	return func() {
		r.mu.Lock()
		defer r.mu.Unlock()
		r.players, r.emailID, r.nameID = players, emails, names
		r.xpEvents, r.presence = events, presence
		r.xpAudit = audit
		r.accountAudit = accounts
		r.pvp = pvp
	}
}

func (r *ActionRepo) Snapshot() func() {
	r.mu.RLock()
	actions, keys := maps.Clone(r.actions), maps.Clone(r.keys)
	r.mu.RUnlock()
	return func() {
		r.mu.Lock()
		defer r.mu.Unlock()
		r.actions, r.keys = actions, keys
	}
}

func (r *MonsterRepo) Snapshot() func() {
	r.mu.RLock()
	items, spawns, loot, nextAI := maps.Clone(r.items), maps.Clone(r.spawns), maps.Clone(r.loot), maps.Clone(r.nextAI)
	events := append([]monster.Event(nil), r.events...)
	r.mu.RUnlock()
	return func() {
		r.mu.Lock()
		defer r.mu.Unlock()
		r.items, r.spawns, r.loot, r.nextAI, r.events = items, spawns, loot, nextAI, events
	}
}

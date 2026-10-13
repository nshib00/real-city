package monster

import (
	"math"
	"time"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/world"
)

type ID string
type SpawnID string
type LootDropID string
type Type string
type State string
type Intent string

const (
	TypeRoamingMelee     Type = "roaming_melee"
	TypeResourceGuardian Type = "resource_guardian"
	TypeRuinsGuardian    Type = "ruins_guardian"
	TypeForestStalker    Type = "forest_stalker"
	TypeSporeBeast       Type = "spore_beast"
	TypeIronbackBrute    Type = "ironback_brute"
	TypeEmberWisp        Type = "ember_wisp"
	TypeAncientColossus  Type = "ancient_colossus"

	StateIdle      State = "idle"
	StateWandering State = "wandering"
	StateAggro     State = "aggro"
	StateAttacking State = "attacking"
	StateDead      State = "dead"

	IntentNone   Intent = "none"
	IntentWander Intent = "wander"
	IntentChase  Intent = "chase"
	IntentAttack Intent = "attack"
)

type Monster struct {
	ID             ID
	MapID          string
	SpawnID        SpawnID
	Type           Type
	State          State
	Tile           world.Coord
	HomeTile       world.Coord
	TargetID       string
	TargetType     string
	Health         int
	MaxHealth      int
	Damage         int
	SpeedTiles     int
	AggroRadius    int
	AttackRange    int
	AttackCooldown time.Duration
	NextAttackAt   time.Time
	LastMovedAt    time.Time
	LootCoins      int
	CreatedAt      time.Time
	UpdatedAt      time.Time
}

type SpawnPoint struct {
	ID          SpawnID
	MapID       string
	Type        Type
	Tile        world.Coord
	Radius      int
	MaxAlive    int
	Cooldown    time.Duration
	NextSpawnAt time.Time
	CreatedAt   time.Time
	UpdatedAt   time.Time
}

type Event struct {
	ID        string
	MonsterID ID
	Type      string
	TargetID  string
	Tile      world.Coord
	CreatedAt time.Time
}

type LootDrop struct {
	ID        LootDropID
	MapID     string
	MonsterID ID
	Tile      world.Coord
	Items     []economy.ResourceAmount
	ClaimedBy string
	CreatedAt time.Time
	ClaimedAt *time.Time
}

type Spec struct {
	Type           Type
	Name           string
	MaxHealth      int
	Damage         int
	SpeedTiles     int
	AggroRadius    int
	AttackRange    int
	AttackCooldown time.Duration
	LootCoins      int
	SpawnWeight    int
}

type Threat struct {
	Tile       world.Coord `json:"tile"`
	Level      int         `json:"level"`
	MonsterIDs []ID        `json:"monster_ids"`
}

type MovementIntent struct {
	Intent Intent
	From   world.Coord
	To     world.Coord
}

func (m Monster) Alive() bool {
	return m.State != StateDead && m.Health > 0
}

func (m Monster) DistanceTo(tile world.Coord) int {
	return int(math.Abs(float64(m.Tile.X-tile.X)) + math.Abs(float64(m.Tile.Y-tile.Y)))
}

func (m Monster) CanAttack(now time.Time, target world.Coord) bool {
	return m.Alive() && m.DistanceTo(target) <= m.AttackRange && !m.NextAttackAt.After(now)
}

func (m *Monster) ApplyDamage(amount int, now time.Time) bool {
	if amount <= 0 || !m.Alive() {
		return false
	}
	m.Health -= amount
	if m.Health <= 0 {
		m.Health = 0
		m.State = StateDead
	}
	m.UpdatedAt = now
	return m.State == StateDead
}

func StepToward(from world.Coord, to world.Coord, speed int) world.Coord {
	if speed <= 0 {
		speed = 1
	}
	next := from
	for range speed {
		dx := to.X - next.X
		dy := to.Y - next.Y
		if dx == 0 && dy == 0 {
			return next
		}
		if abs(dx) >= abs(dy) {
			next.X += sign(dx)
		} else {
			next.Y += sign(dy)
		}
	}
	return next
}

func WanderFrom(home world.Coord, tick int64, radius int) world.Coord {
	if radius <= 0 {
		radius = 3
	}
	offsets := []world.Coord{{X: 1}, {Y: 1}, {X: -1}, {Y: -1}, {X: 1, Y: -1}, {X: -1, Y: 1}}
	offset := offsets[int(tick)%len(offsets)]
	next := world.Coord{X: home.X + offset.X, Y: home.Y + offset.Y}
	if abs(next.X-home.X)+abs(next.Y-home.Y) > radius {
		return home
	}
	return next
}

func abs(value int) int {
	if value < 0 {
		return -value
	}
	return value
}

func sign(value int) int {
	switch {
	case value > 0:
		return 1
	case value < 0:
		return -1
	default:
		return 0
	}
}

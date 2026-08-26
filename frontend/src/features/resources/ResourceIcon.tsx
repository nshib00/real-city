import { Atom, BrickWall, Cable, Coins, Droplet, Flame, FlaskConical, Gem, Hammer, Leaf, Mountain, Package, Pickaxe, Scroll, Sprout, TreePine, UsersRound, Wheat, Zap } from 'lucide-react'

const icons = {
  population: UsersRound,
  coins: Coins,
  'aeolian-crystal': Gem,
  wood: TreePine,
  stone: Mountain,
  stone_block: BrickWall,
  brick: BrickWall,
  oil: Droplet,
  fuel: Flame,
  metal: Mountain,
  glass: Gem,
  clay: Package,
  sand: Mountain,
  coal: Flame,
  iron_ore: Pickaxe,
  iron: Hammer,
  steel: Hammer,
  copper: Cable,
  concrete: BrickWall,
  cement: Package,
  planks: TreePine,
  boards: TreePine,
  fabric: Scroll,
  fiber: Wheat,
  resin: Droplet,
  herbs: Leaf,
  windleaf: Leaf,
  mushrooms: Sprout,
  seeds: Sprout,
  sulfur: FlaskConical,
  explosives: Atom,
  electronics: Zap,
  'super-seeds': Sprout,
  'super-fiber': Wheat,
  'super-mushrooms': Sprout,
} as const

type ResourceIconProps = {
  id: string
  label: string
}

export function ResourceIcon({ id, label }: ResourceIconProps) {
  const Icon = icons[id as keyof typeof icons] ?? Package
  return (
    <span className={`resource-icon resource-icon-${id}`} title={label} aria-label={label}>
      <Icon size={18} aria-hidden="true" />
    </span>
  )
}

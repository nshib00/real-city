import { healthBarColor, healthRatio } from './health'

type HealthBarProps = {
  health: number
  maxHealth: number
}

export function HealthBar({ health, maxHealth }: HealthBarProps) {
  const ratio = healthRatio(health, maxHealth)
  return (
    <div className="health-bar" role="progressbar" aria-label="Здоровье" aria-valuemin={0} aria-valuemax={maxHealth} aria-valuenow={Math.max(0, Math.min(health, maxHealth))}>
      <div className="health-bar-fill" style={{ width: `${ratio * 100}%`, backgroundColor: `#${healthBarColor(ratio).toString(16).padStart(6, '0')}` }} />
    </div>
  )
}

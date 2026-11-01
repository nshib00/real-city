import type { SVGProps } from 'react'
import { iconPaths } from './iconPaths'
import { iconPaths16 } from './iconPaths16'

export type AeolianIconProps = Omit<SVGProps<SVGSVGElement>, 'name'> & {
  name: string
  size?: number | string
  label?: string
}

/** Декоративный по умолчанию; смысловой знак получает label. Неизвестный ключ безопасен. */
export function AeolianIcon({ name, size = 24, label, ...props }: AeolianIconProps) {
  const small = Number(size) > 0 && Number(size) <= 16
  const paths = small ? iconPaths16 : iconPaths
  const path = Object.prototype.hasOwnProperty.call(paths, name)
    ? paths[name as keyof typeof paths] : paths.shortage
  return <svg width={size} height={size} viewBox={small ? '0 0 16 16' : '0 0 24 24'} fill="none" stroke="currentColor" strokeWidth={small ? 1.5 : 1.8} strokeLinejoin="bevel" strokeLinecap="round" focusable="false" {...props} role={label ? 'img' : undefined} aria-label={label} aria-hidden={label ? undefined : true}>
    <path d={path} />
  </svg>
}

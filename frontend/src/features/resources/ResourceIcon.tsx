import { useEffect, useState } from 'react'
import { Package } from '../../shared/ui/icons'
import { resourceCatalog } from '../../../../shared/catalog/resources'

type ResourceIconProps = {
  id: string
  label: string
  className?: string
  decorative?: boolean
  iconVariant?: 'default' | 'asset'
}

export const RESOURCE_ICON_ASSET_REVISION = 'resource-icons-webp-2026-11-01'
const knownResources = new Set(resourceCatalog.map((item) => item.id))
// Старые имена файлов сохранены после переименования ресурсов в каталоге.
const legacyNames: Record<string, string> = { quiet_powder: 'silent_powder', plant_oil: 'vegetable_oil', oleoresin: 'sap', fine_rope: 'rope', tile: 'runic_tile' }

export function resourceIconUrl(id: string) {
  if (!knownResources.has(id)) return `/assets/ui/icons/shortage.svg?v=${RESOURCE_ICON_ASSET_REVISION}`
  if (id === 'kaolin') return '/assets/resources/icons/kaolin.svg'
  return `/assets/resources/icons/runtime/${legacyNames[id] ?? id}.webp?v=${RESOURCE_ICON_ASSET_REVISION}`
}

export function ResourceIcon({ id, label, className, decorative = false, iconVariant = 'default' }: ResourceIconProps) {
  const [renderedIconAvailable, setRenderedIconAvailable] = useState(true)

  useEffect(() => {
    setRenderedIconAvailable(true)
  }, [id])

  return (
    <span className={`resource-icon resource-icon-${id}${className ? ` ${className}` : ''}`} title={label} role={decorative ? undefined : 'img'} aria-hidden={decorative || undefined} aria-label={decorative ? undefined : label}>
      {id === 'population' && iconVariant !== 'asset' ? (
        <svg className="resource-icon-render resource-icon-svg" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path d="M5 4h4v5H5zM3 21v-7l2-2h4l2 2v7m4-15h4v5h-4zm-2 15v-5l2-2h4l2 2v5" />
        </svg>
      ) : renderedIconAvailable ? (
        <img
          src={resourceIconUrl(id)}
          alt=""
          aria-hidden="true"
          className="resource-icon-render"
          width={32}
          height={32}
          decoding="async"
          onError={() => setRenderedIconAvailable(false)}
        />
      ) : (
        <Package size={18} aria-hidden="true" />
      )}
    </span>
  )
}

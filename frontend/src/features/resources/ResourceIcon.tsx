import { useEffect, useState } from 'react'
import { Package } from 'lucide-react'

type ResourceIconProps = {
  id: string
  label: string
  className?: string
}

export const RESOURCE_ICON_ASSET_REVISION = 'weapon-icons-2026-10-25'

export function resourceIconUrl(id: string) {
  if (id === 'kaolin') {
    return '/assets/resources/icons/kaolin.svg'
  }
  return `/assets/resources/icons/${id}.png?v=${RESOURCE_ICON_ASSET_REVISION}`
}

export function ResourceIcon({ id, label, className }: ResourceIconProps) {
  const [renderedIconAvailable, setRenderedIconAvailable] = useState(true)

  useEffect(() => {
    setRenderedIconAvailable(true)
  }, [id])

  return (
    <span className={`resource-icon resource-icon-${id}${className ? ` ${className}` : ''}`} title={label} aria-label={label}>
      {renderedIconAvailable ? (
        <img
          src={resourceIconUrl(id)}
          alt=""
          aria-hidden="true"
          className="resource-icon-render"
          onError={() => setRenderedIconAvailable(false)}
        />
      ) : (
        <Package size={18} aria-hidden="true" />
      )}
    </span>
  )
}

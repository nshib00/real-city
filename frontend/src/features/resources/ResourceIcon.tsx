import { useEffect, useState } from 'react'
import { Package } from 'lucide-react'

type ResourceIconProps = {
  id: string
  label: string
}

export function resourceIconUrl(id: string) {
  return `/assets/resources/icons/${id}.png`
}

export function ResourceIcon({ id, label }: ResourceIconProps) {
  const [renderedIconAvailable, setRenderedIconAvailable] = useState(true)

  useEffect(() => {
    setRenderedIconAvailable(true)
  }, [id])

  return (
    <span className={`resource-icon resource-icon-${id}`} title={label} aria-label={label}>
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

type SegmentItem<T extends string> = {
  id: T
  label: string
}

type SegmentedControlProps<T extends string> = {
  items: readonly SegmentItem<T>[]
  value: T
  onChange: (value: T) => void
  label: string
}

export function SegmentedControl<T extends string>({ items, value, onChange, label }: SegmentedControlProps<T>) {
  return (
    <div className="segmented-control" aria-label={label}>
      {items.map((item) => (
        <button
          className={item.id === value ? 'segment-button segment-button-active' : 'segment-button'}
          key={item.id}
          type="button"
          aria-pressed={item.id === value}
          onClick={() => onChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}

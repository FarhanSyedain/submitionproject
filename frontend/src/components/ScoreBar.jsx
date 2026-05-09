/**
 * Visual 1–10 score bar — flat Apple-style.
 * `invert` flips the colour so high values look bad
 * (used for "effort" where high = more work).
 */
export default function ScoreBar({ value, label, invert = false }) {
  if (value == null) return <span className="text-xs muted">—</span>
  const pct = Math.max(0, Math.min(100, (value / 10) * 100))
  const good = invert ? value <= 4 : value >= 7
  const bad = invert ? value >= 7 : value <= 3

  // Apple system colour palette — System Green / Red / Blue (dark variants).
  const fill = good
    ? 'linear-gradient(90deg, #30d158 0%, #4ade80 100%)'
    : bad
    ? 'linear-gradient(90deg, #ff453a 0%, #ff6961 100%)'
    : 'linear-gradient(90deg, #64d2ff 0%, #0a84ff 60%, #5e5ce6 100%)'

  const valueColor = good ? '#30d158' : bad ? '#ff453a' : '#64d2ff'

  return (
    <div>
      <div
        className="mb-1 flex items-baseline justify-between text-[11px]"
        style={{ letterSpacing: '0.005em' }}
      >
        <span className="muted">{label}</span>
        <span style={{ color: valueColor, fontVariantNumeric: 'tabular-nums' }}>
          {value}
          <span className="muted">/10</span>
        </span>
      </div>
      <div
        className="h-1 overflow-hidden rounded-full"
        style={{ background: 'rgba(255, 255, 255, 0.08)' }}
      >
        <div
          className="h-full rounded-full"
          style={{
            width: `${pct}%`,
            background: fill,
            transition: 'width 600ms cubic-bezier(0.65, 0, 0.35, 1)',
          }}
        />
      </div>
    </div>
  )
}

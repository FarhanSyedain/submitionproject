/**
 * Loading primitives.
 *
 * <Spinner />              — small inline ring spinner
 * <Spinner label="…" />    — ring + label (for inline status rows)
 * <Dots />                 — three pulsing dots, good for "Translating…"
 * <Skeleton lines={3} />   — block placeholder for cards / paragraphs
 * <ProgressBar />          — indeterminate sweeping bar
 */

export default function Spinner({ label, size = 16 }) {
  return (
    <div className="inline-flex items-center gap-2">
      <span
        className="spinner"
        style={{ width: size, height: size }}
        aria-hidden
      />
      {label && <span className="text-sm muted">{label}</span>}
    </div>
  )
}

export function Dots({ label, className = '' }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-sm muted ${className}`}
    >
      {label}
      <span className="loading-dots" aria-hidden>
        <span />
        <span />
        <span />
      </span>
    </span>
  )
}

export function Skeleton({
  lines = 3,
  className = '',
  height = 12,
  gap = 10,
}) {
  return (
    <div
      className={`flex flex-col ${className}`}
      style={{ gap }}
      role="status"
      aria-label="Loading"
    >
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton-line"
          style={{
            height,
            width: i === lines - 1 ? '60%' : '100%',
          }}
        />
      ))}
    </div>
  )
}

export function ProgressBar({ label }) {
  return (
    <div className="w-full">
      {label && (
        <div className="mb-1.5 text-xs muted">{label}</div>
      )}
      <div className="progress-track">
        <div className="progress-bar" />
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'

import { Skeleton } from '../../components/Spinner.jsx'
import { getCompetitors } from '../../api/client.js'

export default function CompetitorsTab({ sessionId, session }) {
  const [items, setItems] = useState(null)
  useEffect(() => {
    getCompetitors(sessionId).then(setItems)
  }, [sessionId, session.status])

  if (items == null) return <ListSkeleton />
  if (items.length === 0)
    return <Empty>No competitors yet. They'll appear once the agent finishes.</Empty>

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {items.map((c) => (
        <div key={c.id} className="glass-card">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="font-semibold">{c.name}</div>
              {c.website && (
                <a
                  href={c.website}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs underline"
                  style={{ color: 'var(--text-accent)' }}
                >
                  {c.website}
                </a>
              )}
            </div>
            <div className="flex flex-wrap items-center justify-end gap-1">
              {c.market_position && (
                <span className="pill capitalize">{c.market_position}</span>
              )}
              {c.estimated_size && (
                <span className="pill capitalize">{c.estimated_size}</span>
              )}
              <span className="pill pill-warn">Threat {c.threat_level}/5</span>
            </div>
          </div>

          {c.description && (
            <p className="mt-3 text-sm muted">{c.description}</p>
          )}

          <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
            <List title="Strengths" items={c.strengths} />
            <List title="Weaknesses" items={c.weaknesses} />
          </div>

          {c.opportunity_gap && (
            <div className="mt-3 rounded-xl p-3 text-sm" style={{ background: 'var(--tint-accent)' }}>
              <span className="font-semibold" style={{ color: 'var(--text-accent)' }}>
                Opportunity gap:{' '}
              </span>
              {c.opportunity_gap}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function List({ title, items }) {
  if (!items || items.length === 0) return null
  return (
    <div>
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide muted">
        {title}
      </div>
      <ul className="space-y-1 text-sm">
        {items.map((it, i) => (
          <li key={i}>• {it}</li>
        ))}
      </ul>
    </div>
  )
}

function Empty({ children }) {
  return <div className="glass-card text-sm muted">{children}</div>
}

function ListSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="glass-card">
          <Skeleton lines={4} height={10} />
        </div>
      ))}
    </div>
  )
}

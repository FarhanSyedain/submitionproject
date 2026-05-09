import { useEffect, useState } from 'react'

import { Skeleton } from '../../components/Spinner.jsx'
import { getTrends } from '../../api/client.js'

const MOMENTUM_PILL = {
  emerging: 'pill pill-accent',
  rising: 'pill pill-good',
  peaking: 'pill pill-warn',
  declining: 'pill pill-bad',
}

export default function TrendsTab({ sessionId, session }) {
  const [items, setItems] = useState(null)
  useEffect(() => {
    getTrends(sessionId).then(setItems)
  }, [sessionId, session.status])

  if (items == null) return <ListSkeleton />
  if (items.length === 0)
    return <div className="glass-card text-sm muted">No trends yet.</div>

  return (
    <div className="space-y-4">
      {items.map((t) => (
        <div key={t.id} className="glass-card">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <div className="font-semibold">{t.title}</div>
              {t.trend_type && (
                <div className="mt-0.5 text-xs muted capitalize">
                  {t.trend_type.replaceAll('_', ' ')}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className={MOMENTUM_PILL[t.momentum] || 'pill'}>{t.momentum}</span>
              {t.relevance_score != null && (
                <span className="pill pill-accent">Relevance {t.relevance_score}/10</span>
              )}
            </div>
          </div>

          {t.description && <p className="mt-3 text-sm muted">{t.description}</p>}

          <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
            {t.opportunity && (
              <div className="rounded-xl p-3 text-sm" style={{ background: 'var(--tint-good)' }}>
                <span className="font-semibold" style={{ color: 'var(--text-success)' }}>
                  Opportunity:{' '}
                </span>
                {t.opportunity}
              </div>
            )}
            {t.threat && (
              <div className="rounded-xl p-3 text-sm" style={{ background: 'var(--tint-bad)' }}>
                <span className="font-semibold" style={{ color: 'var(--text-danger)' }}>
                  Threat:{' '}
                </span>
                {t.threat}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function ListSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2].map((i) => (
        <div key={i} className="glass-card">
          <Skeleton lines={3} height={10} />
        </div>
      ))}
    </div>
  )
}

import { useEffect, useState } from 'react'

import {
  getCompetitors,
  getIdeas,
  getReport,
  getTrends,
} from '../../api/client.js'

export default function OverviewTab({ sessionId, session }) {
  const [counts, setCounts] = useState({ competitors: 0, trends: 0, ideas: 0 })
  const [topIdeas, setTopIdeas] = useState([])
  const [report, setReport] = useState(null)

  useEffect(() => {
    Promise.all([
      getCompetitors(sessionId),
      getTrends(sessionId),
      getIdeas(sessionId),
      getReport(sessionId).catch(() => null),
    ]).then(([c, t, i, r]) => {
      setCounts({ competitors: c.length, trends: t.length, ideas: i.length })
      const sorted = [...i].sort(
        (a, b) => (Number(b.overall_score) || 0) - (Number(a.overall_score) || 0),
      )
      setTopIdeas(sorted.slice(0, 3))
      setReport(r)
    })
  }, [sessionId, session.status])

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Competitors" value={counts.competitors} />
        <Stat label="Trends" value={counts.trends} />
        <Stat label="Ideas" value={counts.ideas} />
        <Stat label="Tokens" value={session.total_tokens} />
      </div>

      {report?.executive_summary && (
        <div className="glass-card">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wide muted">
            Executive summary
          </div>
          <p className="text-sm leading-relaxed">{report.executive_summary}</p>
        </div>
      )}

      {topIdeas.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide muted">
            Top scoring ideas
          </h3>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            {topIdeas.map((i) => (
              <div key={i.id} className="glass-card">
                <div className="flex items-start justify-between gap-2">
                  <div className="font-semibold">{i.title}</div>
                  {i.overall_score != null && (
                    <span className="pill pill-accent">{i.overall_score}</span>
                  )}
                </div>
                <p className="mt-2 line-clamp-3 text-sm muted">{i.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="glass-card">
      <div className="text-xs uppercase tracking-wide muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  )
}

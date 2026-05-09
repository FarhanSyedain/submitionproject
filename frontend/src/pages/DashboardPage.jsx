import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import PageHeader from '../components/PageHeader.jsx'
import { Skeleton } from '../components/Spinner.jsx'
import StatusPill from '../components/StatusPill.jsx'
import { listBusinesses, listSessions } from '../api/client.js'

export default function DashboardPage() {
  const [businesses, setBusinesses] = useState([])
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([listBusinesses(), listSessions()])
      .then(([biz, sess]) => {
        setBusinesses(biz.results ?? biz)
        setSessions(sess)
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <DashboardSkeleton />
  if (error)
    return (
      <div className="glass-card text-sm" style={{ color: 'var(--text-danger)' }}>
        Failed to load: {String(error.message || error)}
      </div>
    )

  const completed = sessions.filter((s) => s.status === 'completed').length

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={`${businesses.length} business${businesses.length === 1 ? '' : 'es'} · ${sessions.length} session${sessions.length === 1 ? '' : 's'} · ${completed} completed`}
        actions={
          <Link to="/analyze/new" className="btn-primary">
            New analysis
          </Link>
        }
      />

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide muted">
          Recent sessions
        </h2>
        {sessions.length === 0 ? (
          <div className="glass-card text-sm muted">
            No analysis sessions yet — start one from{' '}
            <Link to="/analyze/new" className="underline" style={{ color: 'var(--text-accent)' }}>
              New analysis
            </Link>
            .
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {sessions.map((s) => (
              <Link
                key={s.id}
                to={`/analysis/${s.id}`}
                className="glass-card-link block"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="font-semibold">{s.business_name}</div>
                  <StatusPill status={s.status} />
                </div>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs muted">
                  <span>{new Date(s.created_at).toLocaleString()}</span>
                  <span>
                    {s.llm_provider} · {s.llm_model}
                  </span>
                  <span>{s.total_tokens} tokens</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="mt-10">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide muted">
          Business profiles
        </h2>
        {businesses.length === 0 ? (
          <div className="glass-card text-sm muted">
            No business profiles yet — create one when you start a new analysis.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {businesses.map((b) => (
              <div key={b.id} className="glass-card">
                <div className="font-semibold">{b.name}</div>
                {b.industry && <div className="mt-1 text-xs muted">{b.industry}</div>}
                <div className="mt-2 line-clamp-3 text-sm muted">{b.description}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div>
      <div className="mb-6 flex items-end justify-between gap-3">
        <div className="flex-1 space-y-2">
          <Skeleton lines={1} height={28} />
          <Skeleton lines={1} height={12} />
        </div>
      </div>
      <div className="mb-3">
        <Skeleton lines={1} height={12} />
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="glass-card">
            <Skeleton lines={3} height={10} />
          </div>
        ))}
      </div>
    </div>
  )
}

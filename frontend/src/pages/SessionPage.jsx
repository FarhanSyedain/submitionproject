import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'

import PageHeader from '../components/PageHeader.jsx'
import Spinner from '../components/Spinner.jsx'
import StatusPill from '../components/StatusPill.jsx'
import { getSession, getSessionStatus, rerunSession } from '../api/client.js'
import { usePolling } from '../hooks/usePolling.js'

const APPLE = [0.65, 0, 0.35, 1]

import CompetitorsTab from './tabs/CompetitorsTab.jsx'
import FeedbackTab from './tabs/FeedbackTab.jsx'
import IdeasTab from './tabs/IdeasTab.jsx'
import OverviewTab from './tabs/OverviewTab.jsx'
import ReportTab from './tabs/ReportTab.jsx'
import TrendsTab from './tabs/TrendsTab.jsx'

const TABS = [
  { id: 'overview', label: 'Overview', component: OverviewTab },
  { id: 'competitors', label: 'Competitors', component: CompetitorsTab },
  { id: 'trends', label: 'Trends', component: TrendsTab },
  { id: 'ideas', label: 'Ideas', component: IdeasTab },
  { id: 'feedback', label: 'Feedback', component: FeedbackTab },
  { id: 'report', label: 'Report', component: ReportTab },
]

const MODULES = ['competitor', 'trends', 'ideation', 'validation', 'report']

export default function SessionPage() {
  const { id } = useParams()
  const [activeTab, setActiveTab] = useState('overview')
  const [session, setSession] = useState(null)
  const [error, setError] = useState(null)
  const [reruning, setReruning] = useState(false)

  // Initial full session fetch.
  useEffect(() => {
    setSession(null)
    getSession(id).then(setSession).catch(setError)
  }, [id])

  // Lightweight polling while running.
  const { data: status } = usePolling(() => getSessionStatus(id), {
    interval: 3000,
    deps: [id],
    stopWhen: (s) => s.status === 'completed' || s.status === 'failed',
  })

  // Merge status into session as it changes.
  useEffect(() => {
    if (status && session) {
      setSession({ ...session, ...status })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status])

  if (error) {
    return (
      <div className="glass-card text-sm" style={{ color: 'var(--text-danger)' }}>
        Failed to load session: {String(error.message || error)}
      </div>
    )
  }
  if (!session) return <Spinner label="Loading session…" />

  const handleRerun = async () => {
    if (reruning) return
    if (!confirm('Re-run will delete existing competitors / trends / ideas and regenerate them. Continue?')) return
    setReruning(true)
    try {
      const fresh = await rerunSession(id)
      setSession(fresh)
    } finally {
      setReruning(false)
    }
  }

  const ActiveComponent = TABS.find((t) => t.id === activeTab).component

  return (
    <div>
      <PageHeader
        title={session.business_name || 'Analysis'}
        subtitle={
          <span className="flex flex-wrap items-center gap-3">
            <StatusPill status={session.status} />
            <span className="text-xs">{session.llm_provider} · {session.llm_model}</span>
            <span className="text-xs">{session.total_tokens} tokens</span>
            <span className="text-xs">
              started {new Date(session.started_at).toLocaleString()}
            </span>
          </span>
        }
        actions={
          <>
            <Link to="/dashboard" className="btn-ghost">Back</Link>
            <button onClick={handleRerun} className="btn-ghost" disabled={reruning}>
              {reruning ? 'Re-running…' : 'Re-run'}
            </button>
          </>
        }
      />

      {/* Per-module pipeline indicator */}
      <div className="glass-card mb-6">
        <div
          className="mb-3 text-[11px] font-semibold uppercase muted"
          style={{ letterSpacing: '0.14em' }}
        >
          Pipeline
        </div>
        <div className="flex flex-wrap gap-2">
          {MODULES.map((m) => (
            <div
              key={m}
              className="flex items-center gap-2 rounded-full px-3 py-1.5 text-[12px]"
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <span className="capitalize" style={{ letterSpacing: '-0.005em' }}>
                {m}
              </span>
              <StatusPill status={session.module_status?.[m] || 'pending'} />
            </div>
          ))}
        </div>
        {session.error_message && (
          <div className="mt-3 text-xs" style={{ color: 'var(--text-danger)' }}>
            {session.error_message}
          </div>
        )}
      </div>

      {/* Tab nav — iOS-style segmented control with sliding active pill */}
      <SegmentedTabs
        tabs={TABS}
        activeId={activeTab}
        onChange={setActiveTab}
      />

      <ActiveComponent session={session} sessionId={id} />
    </div>
  )
}

/**
 * iOS segmented control. The active pill animates between tabs via
 * framer-motion's shared `layoutId` so the indicator slides instead of
 * jump-cutting. Uses the Apple cubic-bezier so the motion feels heavy.
 */
function SegmentedTabs({ tabs, activeId, onChange }) {
  return (
    <div
      className="mb-6 inline-flex flex-wrap gap-1 p-1"
      style={{
        background: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 999,
        border: '1px solid rgba(255, 255, 255, 0.08)',
      }}
    >
      {tabs.map((t) => {
        const active = activeId === t.id
        return (
          <button
            key={t.id}
            onClick={() => onChange(t.id)}
            className="relative px-4 py-1.5 text-[13px] font-semibold"
            style={{
              color: active ? 'var(--ink)' : 'var(--ink-muted)',
              background: 'transparent',
              border: 0,
              borderRadius: 999,
              letterSpacing: '-0.005em',
              cursor: 'pointer',
              transition: 'color 220ms cubic-bezier(0.65, 0, 0.35, 1)',
              minWidth: 90,
            }}
          >
            {active && (
              <motion.span
                layoutId="segmented-active"
                className="absolute inset-0 -z-0"
                transition={{ duration: 0.4, ease: APPLE }}
                style={{
                  background: 'rgba(255, 255, 255, 0.10)',
                  borderRadius: 999,
                  border: '1px solid rgba(255, 255, 255, 0.10)',
                  boxShadow: '0 4px 12px -4px rgba(0, 0, 0, 0.4)',
                }}
              />
            )}
            <span className="relative z-10">{t.label}</span>
          </button>
        )
      })}
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'

import ScoreBar from '../../components/ScoreBar.jsx'
import Spinner, { Skeleton } from '../../components/Spinner.jsx'
import { getIdeas, updateIdea } from '../../api/client.js'

const VERDICT_PILL = {
  strong_yes: 'pill pill-good',
  yes: 'pill pill-good',
  maybe: 'pill pill-warn',
  no: 'pill pill-bad',
}

const SORTS = [
  { id: 'score', label: 'Top score' },
  { id: 'saved', label: 'Saved first' },
  { id: 'recent', label: 'Most recent' },
]

export default function IdeasTab({ sessionId, session }) {
  const [items, setItems] = useState(null)
  const [sort, setSort] = useState('score')
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    getIdeas(sessionId).then(setItems)
  }, [sessionId, session.status])

  const sorted = useMemo(() => {
    if (!items) return []
    const filtered = filter === 'all' ? items : items.filter((i) => i.category === filter)
    if (sort === 'score') {
      return [...filtered].sort(
        (a, b) => (Number(b.overall_score) || 0) - (Number(a.overall_score) || 0),
      )
    }
    if (sort === 'saved') {
      return [...filtered].sort(
        (a, b) => Number(b.is_saved) - Number(a.is_saved),
      )
    }
    return [...filtered].sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at),
    )
  }, [items, sort, filter])

  if (items == null) return <IdeasSkeleton />
  if (items.length === 0)
    return <div className="glass-card text-sm muted">No ideas yet.</div>

  const categories = Array.from(new Set(items.map((i) => i.category).filter(Boolean)))

  const handleSave = async (idea) => {
    const next = await updateIdea(idea.id, { is_saved: !idea.is_saved })
    setItems(items.map((i) => (i.id === idea.id ? { ...i, ...next } : i)))
  }

  const handleRate = async (idea, rating) => {
    const next = await updateIdea(idea.id, { user_rating: rating })
    setItems(items.map((i) => (i.id === idea.id ? { ...i, ...next } : i)))
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex gap-1">
          {SORTS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSort(s.id)}
              className={sort === s.id ? 'btn-primary' : 'btn-ghost'}
            >
              {s.label}
            </button>
          ))}
        </div>
        <select
          className="select max-w-[200px]"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c.replaceAll('_', ' ')}
            </option>
          ))}
        </select>
        <span className="text-xs muted">
          {sorted.length} of {items.length}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {sorted.map((i) => (
          <IdeaCard
            key={i.id}
            idea={i}
            onSave={() => handleSave(i)}
            onRate={(r) => handleRate(i, r)}
          />
        ))}
      </div>
    </div>
  )
}

function IdeaCard({ idea, onSave, onRate }) {
  const [expanded, setExpanded] = useState(false)
  const v = idea.validation
  return (
    <div className="glass-card">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="font-semibold">{idea.title}</div>
            {idea.category && (
              <span className="pill capitalize">
                {idea.category.replaceAll('_', ' ')}
              </span>
            )}
            {v?.verdict && (
              <span className={VERDICT_PILL[v.verdict] || 'pill'}>
                {v.verdict.replaceAll('_', ' ')}
              </span>
            )}
          </div>
          {idea.source && (
            <div className="mt-1 text-[11px] muted capitalize">
              source: {idea.source.replaceAll('_', ' ')}
            </div>
          )}
        </div>
        <div className="text-right">
          {idea.overall_score != null && (
            <div className="text-2xl font-semibold">{idea.overall_score}</div>
          )}
          <div className="text-[10px] uppercase tracking-wide muted">overall</div>
        </div>
      </div>

      <p className="mt-3 text-sm">{idea.description}</p>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <ScoreBar value={idea.feasibility_score} label="Feasibility" />
        <ScoreBar value={idea.market_fit_score} label="Market fit" />
        <ScoreBar value={idea.effort_score} label="Effort" invert />
        <ScoreBar value={idea.roi_score} label="ROI" />
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              onClick={() => onRate(n)}
              className="text-lg leading-none"
              style={{
                color: idea.user_rating >= n ? '#eab308' : 'rgba(163,177,198,0.5)',
              }}
              aria-label={`Rate ${n}`}
            >
              ★
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setExpanded((e) => !e)}
            className="btn-ghost"
          >
            {expanded ? 'Hide details' : 'Details'}
          </button>
          <button
            onClick={onSave}
            className={idea.is_saved ? 'btn-primary' : 'btn-ghost'}
          >
            {idea.is_saved ? 'Saved' : 'Save'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 space-y-3 pt-4 text-sm" style={{ borderTop: '1px solid rgba(163,177,198,0.3)' }}>
          {idea.time_to_implement && (
            <div>
              <span className="text-xs uppercase tracking-wide muted">Time:</span>{' '}
              {idea.time_to_implement}
            </div>
          )}
          {idea.required_resources?.length > 0 && (
            <Bullets title="Resources" items={idea.required_resources} />
          )}
          {idea.next_steps?.length > 0 && (
            <Bullets title="Next steps" items={idea.next_steps} />
          )}
          {idea.risks?.length > 0 && <Bullets title="Risks" items={idea.risks} />}
          {v?.validation_summary && (
            <div className="rounded-xl p-3 text-sm" style={{ background: 'var(--tint-accent)' }}>
              <span className="font-semibold" style={{ color: 'var(--text-accent)' }}>
                Verdict:{' '}
              </span>
              {v.validation_summary}
            </div>
          )}
          {v?.go_to_market && (
            <div>
              <span className="text-xs uppercase tracking-wide muted">GTM:</span>{' '}
              {v.go_to_market}
            </div>
          )}
          {v?.revenue_potential && (
            <div>
              <span className="text-xs uppercase tracking-wide muted">Revenue:</span>{' '}
              {v.revenue_potential}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Bullets({ title, items }) {
  return (
    <div>
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide muted">
        {title}
      </div>
      <ul className="space-y-1">
        {items.map((it, i) => (
          <li key={i}>• {it}</li>
        ))}
      </ul>
    </div>
  )
}

function IdeasSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="glass-card">
          <Skeleton lines={5} height={10} />
        </div>
      ))}
    </div>
  )
}

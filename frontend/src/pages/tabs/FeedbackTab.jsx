import { useEffect, useState } from 'react'

import Spinner from '../../components/Spinner.jsx'
import { getFeedback, submitFeedback } from '../../api/client.js'

const SENTIMENT_PILL = {
  positive: 'pill pill-good',
  neutral: 'pill',
  negative: 'pill pill-bad',
}

const PRIORITY_PILL = {
  low: 'pill',
  medium: 'pill pill-accent',
  high: 'pill pill-warn',
  critical: 'pill pill-bad',
}

export default function FeedbackTab({ sessionId }) {
  const [submissions, setSubmissions] = useState(null)
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    getFeedback(sessionId).then(setSubmissions)
  }, [sessionId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      await submitFeedback(sessionId, text)
      const fresh = await getFeedback(sessionId)
      setSubmissions(fresh)
      setText('')
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="glass-card space-y-3">
        <div>
          <label className="label">Paste reviews, support tickets, or any customer feedback</label>
          <textarea
            className="textarea"
            rows={6}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="One per line works great. The agent will extract pain points, requests, and sentiment."
          />
        </div>
        {error && (
          <div className="text-sm" style={{ color: 'var(--text-danger)' }}>
            {error}
          </div>
        )}
        <div className="flex justify-end">
          <button type="submit" className="btn-primary" disabled={submitting || !text.trim()}>
            {submitting ? <Spinner /> : null}
            {submitting ? 'Analyzing…' : 'Analyze feedback'}
          </button>
        </div>
      </form>

      {submissions == null ? (
        <Spinner label="Loading feedback…" />
      ) : submissions.length === 0 ? (
        <div className="glass-card text-sm muted">
          No feedback submitted yet. Paste some above to extract structured insights.
        </div>
      ) : (
        <div className="space-y-4">
          {submissions.map((sub) => (
            <div key={sub.id} className="glass-card">
              <div className="flex items-start justify-between gap-2">
                <div className="text-xs muted">
                  {new Date(sub.created_at).toLocaleString()} · {sub.source_type}
                </div>
                <span className="pill">{sub.insights?.length || 0} insights</span>
              </div>
              <div className="glass-card-sunken mt-2 max-h-32 overflow-auto text-xs">
                {sub.raw_text}
              </div>

              {sub.insights?.length > 0 && (
                <div className="mt-4 space-y-3">
                  {sub.insights.map((ins) => (
                    <div key={ins.id} className="glass-card-soft">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div className="font-semibold text-sm">{ins.title}</div>
                        <div className="flex flex-wrap gap-1">
                          <span className="pill capitalize">{ins.insight_type.replaceAll('_', ' ')}</span>
                          <span className={SENTIMENT_PILL[ins.sentiment] || 'pill'}>{ins.sentiment}</span>
                          <span className={PRIORITY_PILL[ins.priority] || 'pill'}>{ins.priority}</span>
                          <span className="pill">×{ins.frequency_score}</span>
                        </div>
                      </div>
                      {ins.description && <p className="mt-2 text-sm muted">{ins.description}</p>}
                      {ins.example_quotes?.length > 0 && (
                        <ul className="mt-2 space-y-1 text-xs italic muted">
                          {ins.example_quotes.map((q, i) => (
                            <li key={i}>“{q}”</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

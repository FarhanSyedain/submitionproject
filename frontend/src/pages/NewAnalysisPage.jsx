/**
 * New analysis — Apple Store-style configurator.
 *
 * The default flow is: create a new business profile → pick a model →
 * start the run. Users with saved profiles can jump in via a small
 * "Use saved" button at the top, which opens an Apple-flavoured popover.
 */
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'

import PageHeader from '../components/PageHeader.jsx'
import Spinner from '../components/Spinner.jsx'
import {
  createBusiness,
  listBusinesses,
  startAnalysis,
} from '../api/client.js'

const APPLE = [0.65, 0, 0.35, 1]

const STAGES = [
  { value: 'idea', label: 'Idea' },
  { value: 'startup', label: 'Startup' },
  { value: 'growth', label: 'Growth' },
  { value: 'enterprise', label: 'Enterprise' },
]

const PROVIDERS = [
  {
    value: 'ollama',
    label: 'Ollama',
    blurb: 'Runs Llama on your own machine. No key, no quota.',
    tag: 'Local',
  },
  {
    value: 'gemini',
    label: 'Gemini',
    blurb: 'Google AI Studio. Free tier is generous, fast.',
    tag: 'Cloud',
  },
  {
    value: 'mock',
    label: 'Mock',
    blurb: 'Instant canned data. Use to preview the UI.',
    tag: 'Dev',
  },
]

export default function NewAnalysisPage() {
  const navigate = useNavigate()
  const [existing, setExisting] = useState([])
  const [savedId, setSavedId] = useState('') // empty = "create new" mode
  const [pickerOpen, setPickerOpen] = useState(false)
  const [form, setForm] = useState({
    name: '',
    description: '',
    industry: '',
    target_market: '',
    location: '',
    stage: 'idea',
    website_url: '',
  })
  const [provider, setProvider] = useState('ollama')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    listBusinesses()
      .then((b) => setExisting(b.results ?? b))
      .catch(() => {
        // empty list is fine
      })
  }, [])

  const handleField = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      let businessId = savedId
      if (!businessId) {
        if (!form.name.trim() || !form.description.trim()) {
          throw new Error('Name and description are required.')
        }
        const created = await createBusiness(form)
        businessId = created.id
      }
      const session = await startAnalysis({
        business_id: businessId,
        llm_provider: provider,
      })
      navigate(`/analysis/${session.id}`)
    } catch (err) {
      setError(err.response?.data || err.message || 'Something went wrong.')
      setSubmitting(false)
    }
  }

  const selectedProfile = existing.find((b) => b.id === savedId)

  return (
    <div>
      <PageHeader
        title="New analysis"
        subtitle="Tell us about the business, pick a model, and we'll run the agents."
        actions={
          existing.length > 0 ? (
            <SavedProfilesPicker
              profiles={existing}
              open={pickerOpen}
              onOpenChange={setPickerOpen}
              selectedId={savedId}
              onSelect={(id) => {
                setSavedId(id)
                setPickerOpen(false)
              }}
            />
          ) : null
        }
      />

      <form onSubmit={handleSubmit} className="space-y-10">
        {/* ─── Step 01 · The business ─────────────────────────────── */}
        <Section
          number="01"
          title={selectedProfile ? 'Selected profile' : 'Tell us about your business'}
          subtitle={
            selectedProfile
              ? "We'll skip the form and use what's saved."
              : "A name and a sentence is enough. Everything else is optional."
          }
        >
          {selectedProfile ? (
            <SelectedProfileCard
              profile={selectedProfile}
              onClear={() => setSavedId('')}
            />
          ) : (
            <BusinessForm form={form} onChange={handleField} />
          )}
        </Section>

        {/* ─── Step 02 · Pick a model ─────────────────────────────── */}
        <Section
          number="02"
          title="Pick a model"
          subtitle="The whole pipeline runs on the model you choose."
        >
          <ProviderCards value={provider} onChange={setProvider} />
        </Section>

        {/* Error block */}
        {error && (
          <div
            className="rounded-2xl px-5 py-4 text-[14px]"
            style={{
              background: 'rgba(255, 69, 58, 0.08)',
              border: '1px solid rgba(255, 69, 58, 0.30)',
              color: 'var(--text-danger)',
            }}
          >
            {typeof error === 'string' ? error : JSON.stringify(error, null, 2)}
          </div>
        )}

        {/* Sticky summary bar — Apple Store "your setup so far" */}
        <SummaryBar
          businessName={selectedProfile?.name || form.name}
          providerLabel={
            PROVIDERS.find((p) => p.value === provider)?.label || provider
          }
          submitting={submitting}
          disabled={
            submitting ||
            (!savedId && (!form.name.trim() || !form.description.trim()))
          }
        />
      </form>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Section — Apple Store step pattern: number + title + subtitle, divider
   ───────────────────────────────────────────────────────────────────── */
function Section({ number, title, subtitle, children }) {
  return (
    <section>
      <div className="mb-6 flex items-baseline gap-4">
        <span
          className="text-[13px] font-semibold tabular-nums"
          style={{ color: 'var(--text-accent)', letterSpacing: '0.04em' }}
        >
          {number}
        </span>
        <div className="flex-1 min-w-0">
          <h2
            className="text-2xl font-semibold leading-tight tracking-tight md:text-[28px]"
            style={{ letterSpacing: '-0.025em' }}
          >
            {title}
          </h2>
          {subtitle && (
            <p
              className="mt-1.5 text-[14px] leading-relaxed muted"
              style={{ letterSpacing: '-0.005em' }}
            >
              {subtitle}
            </p>
          )}
        </div>
      </div>
      <div>{children}</div>
    </section>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Saved profiles picker — small button + Apple popover
   ───────────────────────────────────────────────────────────────────── */
function SavedProfilesPicker({
  profiles,
  open,
  onOpenChange,
  selectedId,
  onSelect,
}) {
  const triggerRef = useRef(null)
  const popoverRef = useRef(null)

  // Click-outside to dismiss
  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (
        popoverRef.current?.contains(e.target) ||
        triggerRef.current?.contains(e.target)
      ) {
        return
      }
      onOpenChange(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open, onOpenChange])

  // Esc to dismiss
  useEffect(() => {
    if (!open) return
    const handler = (e) => e.key === 'Escape' && onOpenChange(false)
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onOpenChange])

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => onOpenChange(!open)}
        className="inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-all"
        style={{
          background: open ? 'rgba(10, 132, 255, 0.16)' : 'rgba(255, 255, 255, 0.06)',
          color: open ? 'var(--text-accent)' : 'var(--ink)',
          border: `1px solid ${
            open ? 'rgba(10, 132, 255, 0.40)' : 'rgba(255, 255, 255, 0.10)'
          }`,
          letterSpacing: '-0.005em',
        }}
      >
        <span>Use saved profile</span>
        <Chevron open={open} />
      </button>

      <AnimatePresence>
        {open && (
          <>
            {/* Backdrop blur — subtle so the rest of the page feels recessed */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2, ease: APPLE }}
              className="fixed inset-0 z-30"
              style={{ backdropFilter: 'blur(2px)' }}
            />
            <motion.div
              ref={popoverRef}
              initial={{ opacity: 0, y: -8, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.96 }}
              transition={{ duration: 0.28, ease: APPLE }}
              role="dialog"
              aria-label="Saved business profiles"
              className="absolute right-0 top-[calc(100%+10px)] z-40 w-[360px]"
              style={{
                background: 'rgba(28, 28, 30, 0.92)',
                backdropFilter: 'saturate(180%) blur(24px)',
                WebkitBackdropFilter: 'saturate(180%) blur(24px)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: 16,
                boxShadow:
                  '0 20px 60px -10px rgba(0, 0, 0, 0.6), 0 8px 24px -8px rgba(0, 0, 0, 0.5)',
              }}
            >
              <div
                className="px-4 py-3"
                style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}
              >
                <div
                  className="text-[11px] font-semibold uppercase muted"
                  style={{ letterSpacing: '0.14em' }}
                >
                  Saved profiles · {profiles.length}
                </div>
              </div>
              <ul className="max-h-[360px] overflow-y-auto p-2">
                {profiles.map((b) => {
                  const selected = b.id === selectedId
                  return (
                    <li key={b.id}>
                      <button
                        type="button"
                        onClick={() => onSelect(b.id)}
                        className="group w-full rounded-xl px-3 py-2.5 text-left transition-all"
                        style={{
                          background: selected
                            ? 'rgba(10, 132, 255, 0.16)'
                            : 'transparent',
                        }}
                        onMouseEnter={(e) => {
                          if (!selected)
                            e.currentTarget.style.background =
                              'rgba(255, 255, 255, 0.06)'
                        }}
                        onMouseLeave={(e) => {
                          if (!selected)
                            e.currentTarget.style.background = 'transparent'
                        }}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div
                              className="text-[14px] font-semibold tracking-tight"
                              style={{
                                color: selected
                                  ? 'var(--text-accent)'
                                  : 'var(--ink)',
                                letterSpacing: '-0.01em',
                              }}
                            >
                              {b.name}
                            </div>
                            {b.industry && (
                              <div className="mt-0.5 text-[12px] muted">
                                {b.industry}
                              </div>
                            )}
                            {b.description && (
                              <div className="mt-1.5 line-clamp-2 text-[12.5px] leading-snug muted">
                                {b.description}
                              </div>
                            )}
                          </div>
                          {selected && <Check />}
                        </div>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

function Chevron({ open }) {
  return (
    <motion.svg
      width="10"
      height="10"
      viewBox="0 0 10 10"
      animate={{ rotate: open ? 180 : 0 }}
      transition={{ duration: 0.25, ease: APPLE }}
    >
      <path
        d="M2 3.5 L5 6.5 L8 3.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </motion.svg>
  )
}

function Check() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 18 18"
      style={{ flex: '0 0 auto', marginTop: 2 }}
    >
      <circle cx="9" cy="9" r="9" fill="#0a84ff" />
      <path
        d="M5 9.5 L8 12 L13 6.5"
        fill="none"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Selected profile card — when a saved profile is in use
   ───────────────────────────────────────────────────────────────────── */
function SelectedProfileCard({ profile, onClear }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: APPLE }}
      className="rounded-2xl p-6"
      style={{
        background: 'rgba(10, 132, 255, 0.06)',
        border: '1px solid rgba(10, 132, 255, 0.25)',
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div
            className="text-[11px] font-semibold uppercase"
            style={{ color: 'var(--text-accent)', letterSpacing: '0.14em' }}
          >
            Using saved profile
          </div>
          <div
            className="mt-1.5 text-[22px] font-semibold leading-tight tracking-tight"
            style={{ letterSpacing: '-0.02em' }}
          >
            {profile.name}
          </div>
          {profile.industry && (
            <div className="mt-1 text-[13px] muted">{profile.industry}</div>
          )}
          {profile.description && (
            <p className="mt-3 text-[14px] leading-relaxed muted">
              {profile.description}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onClear}
          className="rounded-full px-3.5 py-1.5 text-[12.5px] font-medium transition-colors"
          style={{
            background: 'rgba(255, 255, 255, 0.08)',
            border: '1px solid rgba(255, 255, 255, 0.10)',
            color: 'var(--ink)',
            letterSpacing: '-0.005em',
            whiteSpace: 'nowrap',
          }}
        >
          Create new instead
        </button>
      </div>
    </motion.div>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Business form — clean Apple Store-style fields
   ───────────────────────────────────────────────────────────────────── */
function BusinessForm({ form, onChange }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: APPLE }}
      className="space-y-5"
    >
      <Field label="Business name" required>
        <input
          className="input"
          value={form.name}
          onChange={onChange('name')}
          placeholder="e.g. Zeaniv AI"
          required
        />
      </Field>
      <Field label="Description" required>
        <textarea
          className="textarea"
          rows={4}
          value={form.description}
          onChange={onChange('description')}
          placeholder="What you sell, who you sell to, and why."
          required
        />
      </Field>
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <Field label="Industry">
          <input
            className="input"
            value={form.industry}
            onChange={onChange('industry')}
            placeholder="SaaS, e-commerce, fintech…"
          />
        </Field>
        <Field label="Target market">
          <input
            className="input"
            value={form.target_market}
            onChange={onChange('target_market')}
            placeholder="Solo founders, SMB, enterprise…"
          />
        </Field>
        <Field label="Location">
          <input
            className="input"
            value={form.location}
            onChange={onChange('location')}
            placeholder="Optional"
          />
        </Field>
        <Field label="Stage">
          <select
            className="select"
            value={form.stage}
            onChange={onChange('stage')}
          >
            {STAGES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </Field>
        <div className="md:col-span-2">
          <Field label="Website">
            <input
              className="input"
              value={form.website_url}
              onChange={onChange('website_url')}
              placeholder="https://…"
            />
          </Field>
        </div>
      </div>
    </motion.div>
  )
}

function Field({ label, required, children }) {
  return (
    <div>
      <label
        className="mb-1.5 block text-[13px] font-medium muted"
        style={{ letterSpacing: '-0.005em' }}
      >
        {label}
        {required && (
          <span style={{ color: 'var(--text-accent)', marginLeft: 4 }}>·</span>
        )}
      </label>
      {children}
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Provider cards — Apple Store-style configuration radio cards
   ───────────────────────────────────────────────────────────────────── */
function ProviderCards({ value, onChange }) {
  return (
    <div role="radiogroup" className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {PROVIDERS.map((p) => {
        const selected = value === p.value
        return (
          <button
            key={p.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(p.value)}
            className="relative overflow-hidden rounded-2xl p-5 text-left transition-all"
            style={{
              background: selected
                ? 'rgba(10, 132, 255, 0.08)'
                : 'rgba(255, 255, 255, 0.04)',
              border: `1.5px solid ${
                selected ? 'rgba(10, 132, 255, 0.55)' : 'rgba(255, 255, 255, 0.08)'
              }`,
              cursor: 'pointer',
              transition: 'all 220ms cubic-bezier(0.65, 0, 0.35, 1)',
            }}
            onMouseEnter={(e) => {
              if (!selected) {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.18)'
              }
            }}
            onMouseLeave={(e) => {
              if (!selected) {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'
              }
            }}
          >
            {selected && (
              <motion.span
                layoutId="provider-selected"
                className="absolute right-4 top-4"
                transition={{ duration: 0.4, ease: APPLE }}
              >
                <Check />
              </motion.span>
            )}
            <div
              className="text-[11px] font-semibold uppercase muted"
              style={{ letterSpacing: '0.14em' }}
            >
              {p.tag}
            </div>
            <div
              className="mt-2 text-[20px] font-semibold tracking-tight"
              style={{
                letterSpacing: '-0.02em',
                color: selected ? 'var(--text-accent)' : 'var(--ink)',
              }}
            >
              {p.label}
            </div>
            <p className="mt-2 text-[13.5px] leading-relaxed muted">{p.blurb}</p>
          </button>
        )
      })}
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Sticky summary bar — Apple Store "your setup so far"
   ───────────────────────────────────────────────────────────────────── */
function SummaryBar({ businessName, providerLabel, submitting, disabled }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: APPLE, delay: 0.1 }}
      className="sticky bottom-4 z-20 rounded-2xl px-5 py-4"
      style={{
        background: 'rgba(28, 28, 30, 0.85)',
        backdropFilter: 'saturate(180%) blur(24px)',
        WebkitBackdropFilter: 'saturate(180%) blur(24px)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        boxShadow: '0 20px 50px -10px rgba(0, 0, 0, 0.6)',
      }}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div
            className="text-[11px] font-semibold uppercase muted"
            style={{ letterSpacing: '0.14em' }}
          >
            Your setup
          </div>
          <div className="mt-1 truncate text-[14px]">
            <span style={{ color: 'var(--ink)' }}>
              {businessName || 'Untitled business'}
            </span>
            <span className="muted"> · {providerLabel}</span>
          </div>
        </div>
        <button type="submit" className="btn-primary" disabled={disabled}>
          {submitting && <Spinner />}
          {submitting ? 'Running…' : 'Start analysis'}
        </button>
      </div>
    </motion.div>
  )
}

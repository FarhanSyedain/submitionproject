import { useEffect, useRef, useState } from 'react'

import Spinner, { Dots, Skeleton } from '../../components/Spinner.jsx'
import {
  exportReportPdf,
  fetchReportAudio,
  getReport,
  translateReport,
} from '../../api/client.js'

const PRIORITY_PILL = {
  high: 'pill pill-bad',
  medium: 'pill pill-warn',
  low: 'pill',
}

// Kashmiri renders best in Nastaliq calligraphic style.
const NASTALIQ_FONT =
  '"Noto Nastaliq Urdu", "Noto Naskh Arabic", "Amiri", "Inter", sans-serif'

// Nastaliq is dense and tall — give it more size, more leading.
const KS_BODY_STYLE = {
  fontFamily: NASTALIQ_FONT,
  fontSize: '22px',
  lineHeight: 2.05,
  letterSpacing: '0.01em',
}
const KS_HEADLINE_STYLE = {
  fontFamily: NASTALIQ_FONT,
  fontSize: '26px',
  lineHeight: 1.95,
  letterSpacing: '0.01em',
}
const KS_LIST_STYLE = {
  fontFamily: NASTALIQ_FONT,
  fontSize: '20px',
  lineHeight: 2.0,
  letterSpacing: '0.01em',
}

const COL_DIVIDER = 'rgba(255, 255, 255, 0.06)'

export default function ReportTab({ sessionId, session }) {
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [exporting, setExporting] = useState(false)

  // Language toggle — 'en' (default) or 'ks'.
  const [lang, setLang] = useState('en')

  // Kashmiri translation — pre-warmed by the backend localiser when ready.
  const [translation, setTranslation] = useState(null)
  const [translating, setTranslating] = useState(false)
  const [translateError, setTranslateError] = useState(null)

  // Audio playback — only fetched once user switches to Kashmiri.
  const [audioUrl, setAudioUrl] = useState(null)
  const [audioLoading, setAudioLoading] = useState(false)
  const [audioError, setAudioError] = useState(null)
  const [playing, setPlaying] = useState(false)
  const audioRef = useRef(null)

  // TTS provider override — picked by the user from the audio card.
  // Default is local_matcha (in-process), with local_http (Modal) as the
  // alternative. Affects regenerations only; the cache wins on first load.
  const [ttsProvider, setTtsProvider] = useState('local_matcha')
  const [regenerating, setRegenerating] = useState(false)

  useEffect(() => {
    setReport(null)
    setError(null)
    setLang('en')
    setTranslation(null)
    setTranslateError(null)
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setAudioUrl(null)
    setAudioError(null)
    setPlaying(false)

    let cancelled = false

    const loadReport = async () => {
      let data
      try {
        data = await getReport(sessionId)
      } catch (e) {
        if (cancelled) return
        if (e.response?.status === 404) setReport({})
        else setError(e)
        return
      }
      if (cancelled) return
      setReport(data)

      if (!data?.executive_summary) return

      // Kashmiri translation — use cached payload when available, else
      // kick off the on-demand translate call in the background. Audio
      // is loaded lazily when the user actually switches to Kashmiri.
      if (data.ks_translation && data.ks_translation.executive_summary) {
        setTranslation(data.ks_translation)
      } else {
        setTranslating(true)
        translateReport(sessionId, 'ks')
          .then((t) => {
            if (!cancelled) setTranslation(t)
          })
          .catch((e) => {
            if (!cancelled)
              setTranslateError(e.response?.data?.detail || e.message)
          })
          .finally(() => {
            if (!cancelled) setTranslating(false)
          })
      }
    }

    loadReport()

    return () => {
      cancelled = true
    }
  }, [sessionId, session.status, session.llm_provider])

  // Fetch the narration blob the first time the user switches to Kashmiri
  // (and keep it cached for the rest of the session).
  //
  // IMPORTANT: do NOT put `audioLoading` in the deps. We set it inside
  // the effect, which would cause the effect to clean-up + re-run mid-
  // fetch, flip its own `cancelled` flag to true, and then silently
  // swallow the response — leaving audioLoading stuck at `true` forever.
  // We also skip while a regenerate is in flight so we don't race a
  // cached fetch against the user's force-resynth.
  useEffect(() => {
    if (
      lang !== 'ks' ||
      audioUrl ||
      regenerating ||
      !report?.ks_audio_available
    ) {
      return
    }
    let cancelled = false
    setAudioLoading(true)
    fetchReportAudio(sessionId, { lang: 'ks', section: 'executive_summary' })
      .then((blob) => {
        if (!cancelled) setAudioUrl(URL.createObjectURL(blob))
      })
      .catch((e) => {
        if (!cancelled) setAudioError(e.response?.data?.detail || e.message)
      })
      .finally(() => {
        if (!cancelled) setAudioLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [lang, sessionId, report?.ks_audio_available, audioUrl, regenerating])

  // Revoke any blob URL we created when the component unmounts / changes.
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl)
    }
  }, [audioUrl])

  // Pause playback when leaving the Kashmiri tab so the audio doesn't
  // keep running in the background.
  useEffect(() => {
    if (lang !== 'ks' && audioRef.current && playing) {
      audioRef.current.pause()
    }
  }, [lang, playing])

  // Force a fresh synthesis with the currently-selected provider. The
  // backend invalidates the cache and writes the new bytes back to it,
  // so subsequent loads serve the fresh audio.
  const handleRegenerate = async () => {
    if (regenerating) return
    setRegenerating(true)
    setAudioError(null)
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
      setAudioUrl(null)
    }
    setPlaying(false)
    try {
      const blob = await fetchReportAudio(sessionId, {
        lang: 'ks',
        section: 'executive_summary',
        provider: ttsProvider,
        force: true,
      })
      setAudioUrl(URL.createObjectURL(blob))
      // Optimistically clear any stale localiser-failure state — the
      // backend just persisted fresh audio + flipped the row to
      // "completed", so subsequent renders shouldn't show the old
      // failure card. The next report fetch will confirm.
      setReport((prev) =>
        prev
          ? {
              ...prev,
              localization_status: 'completed',
              localization_error: '',
              ks_audio_available: true,
            }
          : prev,
      )
    } catch (e) {
      setAudioError(e.response?.data?.detail || e.message)
    } finally {
      setRegenerating(false)
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const blob = await exportReportPdf(sessionId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `zeaniv-report-${session.business_name || 'report'}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert(`PDF export failed: ${e.message}`)
    } finally {
      setExporting(false)
    }
  }

  if (error)
    return (
      <div className="glass-card text-sm" style={{ color: 'var(--text-danger)' }}>
        Failed to load report: {String(error.message || error)}
      </div>
    )
  if (report == null) return <ReportSkeleton />
  if (!report.executive_summary)
    return (
      <div className="glass-card text-sm muted">
        Report not generated yet — wait for the pipeline to finish, or hit{' '}
        <strong>Re-run</strong>.
      </div>
    )

  const localizationStatus = report.localization_status || ''
  const localizationInProgress =
    localizationStatus === 'pending' || localizationStatus === 'running'
  const localizationFailed = localizationStatus === 'failed'

  const ks =
    translation && translation.lang === 'ks' && translation.executive_summary
      ? translation
      : null
  const ksReady = Boolean(ks)

  // What we actually render — switch between English (from `report`) and
  // Kashmiri (from `translation`).
  const showingKs = lang === 'ks' && ksReady
  const summaryText = showingKs ? ks.executive_summary : report.executive_summary
  const insights = showingKs ? ks.key_insights : report.key_insights
  const actions = showingKs ? ks.recommended_actions : report.recommended_actions

  return (
    <div className="space-y-6">
      {/* Toolbar — language toggle + PDF export */}
      <div className="glass-card flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-xs uppercase tracking-wide muted">Language</span>
          <LanguageSwitch
            lang={lang}
            onChange={setLang}
            ksReady={ksReady}
            ksTranslating={translating}
            ksError={translateError}
          />
        </div>

        <button
          onClick={handleExport}
          disabled={exporting}
          className="btn-primary"
        >
          {exporting && <Spinner />}
          {exporting ? 'Exporting…' : 'Export PDF'}
        </button>
      </div>

      {/* Audio — only visible on the Kashmiri tab */}
      {lang === 'ks' && (
        <AudioControl
          url={audioUrl}
          loading={audioLoading}
          error={audioError}
          playing={playing}
          setPlaying={setPlaying}
          audioRef={audioRef}
          localizationInProgress={localizationInProgress}
          localizationFailed={localizationFailed}
          localizationError={report.localization_error}
          ttsProvider={ttsProvider}
          onTtsProviderChange={setTtsProvider}
          onRegenerate={handleRegenerate}
          regenerating={regenerating}
        />
      )}

      {/* ── Executive summary — the headline section ───────────────── */}
      <div className="glass-card">
        <SectionHeader title="Executive summary" />
        {showingKs ? (
          <p style={KS_HEADLINE_STYLE} dir="rtl">
            {summaryText}
          </p>
        ) : (
          <p
            className="text-[17px] leading-[1.75]"
            style={{ color: 'var(--text-primary)' }}
          >
            {summaryText}
          </p>
        )}
      </div>

      {/* ── Key insights ───────────────────────────────────────────── */}
      {insights?.length > 0 && (
        <div className="glass-card">
          <SectionHeader title="Key insights" />
          {showingKs ? (
            <ul className="space-y-3" dir="rtl">
              {insights.map((insight, i) => (
                <li key={i} className="flex gap-3" style={KS_LIST_STYLE}>
                  <span
                    style={{
                      color: 'var(--text-accent)',
                      fontFamily: 'system-ui',
                    }}
                  >
                    ◂
                  </span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          ) : (
            <ul className="space-y-3">
              {insights.map((insight, i) => (
                <li key={i} className="flex gap-3 text-[15px] leading-relaxed">
                  <span style={{ color: 'var(--text-accent)' }}>▸</span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* ── Recommended actions ────────────────────────────────────── */}
      {actions?.length > 0 && (
        <div className="glass-card">
          <SectionHeader title="Recommended actions" />
          <div className="space-y-3">
            {actions.map((a, i) => (
              <div key={i} className="glass-card-sunken">
                <div className="flex flex-wrap items-start gap-3">
                  <span
                    className="text-xs font-semibold tabular-nums"
                    style={{
                      color: 'var(--text-accent)',
                      minWidth: '1.5rem',
                    }}
                  >
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={PRIORITY_PILL[a.priority] || 'pill'}>
                        {a.priority}
                      </span>
                      {a.timeline && (
                        <span className="text-xs muted">{a.timeline}</span>
                      )}
                    </div>
                    {showingKs ? (
                      <p style={KS_BODY_STYLE} dir="rtl">
                        {a.action}
                      </p>
                    ) : (
                      <p className="text-[15px] leading-relaxed">{a.action}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   LanguageSwitch — two-pill toggle. Kashmiri pill is disabled while the
   translation is still being prepared, and surfaces the error if it fails.
   ───────────────────────────────────────────────────────────────────── */
function LanguageSwitch({ lang, onChange, ksReady, ksTranslating, ksError }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex gap-1">
        <button
          type="button"
          onClick={() => onChange('en')}
          className={lang === 'en' ? 'btn-primary' : 'btn-ghost'}
        >
          English
        </button>
        <button
          type="button"
          onClick={() => onChange('ks')}
          disabled={!ksReady}
          className={lang === 'ks' ? 'btn-primary' : 'btn-ghost'}
          style={{ fontFamily: NASTALIQ_FONT, fontSize: '15px' }}
        >
          کٲشُر
        </button>
      </div>
      {!ksReady && ksTranslating && <Dots label="Preparing" />}
      {!ksReady && ksError && (
        <span className="text-xs" style={{ color: 'var(--text-danger)' }}>
          {ksError}
        </span>
      )}
    </div>
  )
}

function SectionHeader({ title }) {
  return (
    <div
      className="mb-5 flex items-baseline justify-between border-b pb-3"
      style={{ borderColor: COL_DIVIDER }}
    >
      <h3
        className="text-[15px] font-semibold tracking-tight"
        style={{ color: 'var(--text-primary)' }}
      >
        {title}
      </h3>
    </div>
  )
}

function ReportSkeleton() {
  return (
    <div className="space-y-6">
      <div className="glass-card">
        <Skeleton lines={2} height={14} />
      </div>
      <div className="glass-card">
        <div className="mb-3 text-xs font-semibold uppercase tracking-wide muted">
          Executive summary
        </div>
        <Skeleton lines={4} height={10} />
      </div>
      <div className="glass-card">
        <div className="mb-3 text-xs font-semibold uppercase tracking-wide muted">
          Key insights
        </div>
        <Skeleton lines={3} height={10} />
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   AudioControl — single button that toggles between Play and Pause.
   The native <audio> element stays in the DOM (so playback works) but
   is hidden; we drive it via the ref and listen to play/pause/ended
   so external state stays in sync if playback ends naturally.
   ───────────────────────────────────────────────────────────────────── */
function AudioControl({
  url,
  loading,
  error,
  playing,
  setPlaying,
  audioRef,
  localizationInProgress,
  localizationFailed,
  localizationError,
  ttsProvider,
  onTtsProviderChange,
  onRegenerate,
  regenerating,
}) {
  // Active synth wins over every other state — even if `report` still
  // says `localization_status === "failed"` from a previous attempt,
  // we want the user to see the live spinner for the regenerate they
  // just kicked off.
  if (regenerating) {
    return (
      <div className="glass-card space-y-3">
        <div className="flex items-center gap-3 text-sm muted">
          <Spinner />
          <span>
            Synthesising via{' '}
            {ttsProvider === 'local_http' ? 'Modal' : 'local Matcha'}…
          </span>
        </div>
        <SourceRow
          ttsProvider={ttsProvider}
          onTtsProviderChange={onTtsProviderChange}
          onRegenerate={onRegenerate}
          regenerating={regenerating}
        />
      </div>
    )
  }
  if (loading) {
    return (
      <div className="glass-card space-y-3">
        <div className="flex items-center gap-3 text-sm muted">
          <Spinner />
          <span>Loading narration…</span>
        </div>
        <SourceRow
          ttsProvider={ttsProvider}
          onTtsProviderChange={onTtsProviderChange}
          onRegenerate={onRegenerate}
          regenerating={regenerating}
        />
      </div>
    )
  }
  if (error) {
    return (
      <div className="glass-card space-y-3">
        <div className="text-sm" style={{ color: 'var(--text-danger)' }}>
          Audio failed: {error}
        </div>
        <SourceRow
          ttsProvider={ttsProvider}
          onTtsProviderChange={onTtsProviderChange}
          onRegenerate={onRegenerate}
          regenerating={regenerating}
        />
      </div>
    )
  }
  // Only surface the localiser failure when we genuinely have no audio
  // to fall back on. A stale "failed" status shouldn't override a fresh
  // regenerate that just produced bytes.
  if (localizationFailed && !url) {
    return (
      <div className="glass-card space-y-3">
        <div className="text-sm" style={{ color: 'var(--text-danger)' }}>
          Couldn’t prepare Kashmiri narration: {localizationError || 'unknown error'}
        </div>
        <SourceRow
          ttsProvider={ttsProvider}
          onTtsProviderChange={onTtsProviderChange}
          onRegenerate={onRegenerate}
          regenerating={regenerating}
        />
      </div>
    )
  }
  if (localizationInProgress && !url) {
    return (
      <div className="glass-card space-y-2">
        <Dots label="Preparing Kashmiri narration" />
        <div className="text-xs muted">
          Translating + synthesising in the background.
        </div>
      </div>
    )
  }
  if (!url) return null

  const togglePlay = () => {
    if (!audioRef.current) return
    if (playing) audioRef.current.pause()
    else audioRef.current.play()
  }

  return (
    <div className="glass-card space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <div className="text-xs font-semibold uppercase tracking-wide muted">
            Narration · کٲشُر
          </div>
          <div className="mt-1 text-xs muted">
            {playing
              ? 'Playing the executive summary in Kashmiri…'
              : 'Tap to hear the executive summary read aloud.'}
          </div>
        </div>
        <button onClick={togglePlay} className="btn-primary">
          {playing ? (
            <>
              <PauseIcon />
              Pause
            </>
          ) : (
            <>
              <PlayIcon />
              Play audio
            </>
          )}
        </button>
      </div>
      <SourceRow
        ttsProvider={ttsProvider}
        onTtsProviderChange={onTtsProviderChange}
        onRegenerate={onRegenerate}
        regenerating={regenerating}
      />
      <audio
        ref={audioRef}
        src={url}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        style={{ display: 'none' }}
      />
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   SourceRow — compact "Source: [Local] [Modal]   ↻ Regenerate" line.
   The toggle picks which TTS provider to hit on the next regenerate.
   ───────────────────────────────────────────────────────────────────── */
function SourceRow({ ttsProvider, onTtsProviderChange, onRegenerate, regenerating }) {
  if (!onTtsProviderChange) return null
  const Pill = ({ value, label }) => (
    <button
      type="button"
      onClick={() => onTtsProviderChange(value)}
      disabled={regenerating}
      aria-pressed={ttsProvider === value}
      className="rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
      style={
        ttsProvider === value
          ? {
              background: 'rgba(10, 132, 255, 0.16)',
              color: 'var(--text-accent)',
              border: '1px solid rgba(10, 132, 255, 0.4)',
            }
          : {
              background: 'transparent',
              color: 'var(--text-muted)',
              border: '1px solid rgba(255, 255, 255, 0.10)',
            }
      }
    >
      {label}
    </button>
  )
  return (
    <div className="flex flex-wrap items-center gap-3 border-t pt-3" style={{ borderColor: COL_DIVIDER }}>
      <span className="text-[11px] uppercase tracking-wide muted">Source</span>
      <div className="flex gap-1">
        <Pill value="local_matcha" label="Local" />
        <Pill value="local_http" label="Modal" />
      </div>
      <div className="ml-auto">
        <button
          type="button"
          onClick={onRegenerate}
          disabled={regenerating}
          className="btn-ghost text-[12px]"
        >
          {regenerating ? <Spinner /> : '↻'} Regenerate
        </button>
      </div>
    </div>
  )
}

function PlayIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M3 1.6a.9.9 0 0 1 1.36-.78l8 4.4a.9.9 0 0 1 0 1.56l-8 4.4A.9.9 0 0 1 3 10.4z" />
    </svg>
  )
}

function PauseIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="currentColor"
      aria-hidden="true"
    >
      <rect x="3" y="2" width="3" height="10" rx="0.8" />
      <rect x="8" y="2" width="3" height="10" rx="0.8" />
    </svg>
  )
}

import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

// ── Businesses ─────────────────────────────────────────────────────────
export const listBusinesses = () => api.get('/api/businesses/').then((r) => r.data)
export const createBusiness = (payload) =>
  api.post('/api/businesses/', payload).then((r) => r.data)
export const getBusiness = (id) => api.get(`/api/businesses/${id}/`).then((r) => r.data)

// ── Analysis sessions ──────────────────────────────────────────────────
export const listSessions = () =>
  api.get('/api/analysis/').then((r) => r.data.results ?? r.data)

export const startAnalysis = ({ business_id, llm_provider }) =>
  api
    .post('/api/analysis/start/', { business_id, llm_provider })
    .then((r) => r.data)

export const getSession = (id) =>
  api.get(`/api/analysis/${id}/`).then((r) => r.data)

export const getSessionStatus = (id) =>
  api.get(`/api/analysis/${id}/status/`).then((r) => r.data)

export const rerunSession = (id) =>
  api.post(`/api/analysis/${id}/rerun/`).then((r) => r.data)

// ── Module data ────────────────────────────────────────────────────────
const unwrap = (r) => r.data.results ?? r.data

export const getCompetitors = (sessionId) =>
  api.get(`/api/analysis/${sessionId}/competitors/`).then(unwrap)

export const getTrends = (sessionId) =>
  api.get(`/api/analysis/${sessionId}/trends/`).then(unwrap)

export const getIdeas = (sessionId) =>
  api.get(`/api/analysis/${sessionId}/ideas/`).then(unwrap)

export const getValidations = (sessionId) =>
  api.get(`/api/analysis/${sessionId}/validation/`).then(unwrap)

export const getReport = (sessionId) =>
  api.get(`/api/analysis/${sessionId}/report/`).then((r) => r.data)

export const getFeedback = (sessionId) =>
  api.get(`/api/analysis/${sessionId}/feedback/`).then(unwrap)

export const submitFeedback = (sessionId, raw_text, source_type = 'manual') =>
  api
    .post(`/api/analysis/${sessionId}/feedback/submit/`, { raw_text, source_type })
    .then((r) => r.data)

// ── Ideas ──────────────────────────────────────────────────────────────
export const updateIdea = (id, payload) =>
  api.patch(`/api/ideas/${id}/`, payload).then((r) => r.data)

// ── Report export ──────────────────────────────────────────────────────
export const exportReportPdf = async (sessionId) => {
  const r = await api.post(`/api/analysis/${sessionId}/report/export/`, null, {
    responseType: 'blob',
  })
  return r.data
}

// ── Translation + TTS ──────────────────────────────────────────────────
export const translateReport = (sessionId, lang = 'ks') =>
  api
    .post(`/api/analysis/${sessionId}/report/translate/`, { lang })
    .then((r) => r.data)

export const fetchReportAudio = async (
  sessionId,
  {
    lang = 'ks',
    section = 'executive_summary',
    provider, // 'local_matcha' | 'local_http' — overrides the server default
    force = false, // bypass cache + persist a fresh synth
  } = {},
) => {
  const body = { lang, section, force }
  if (provider) body.provider = provider
  const r = await api.post(
    `/api/analysis/${sessionId}/report/audio/`,
    body,
    {
      responseType: 'blob',
      // Local Matcha runs at the full 1500 diffusion steps and synth time
      // scales roughly linearly: ~150 s on M-series MPS for the typical
      // summary, longer when busy. Modal stays much faster (clamped to
      // 150 steps), but the same timeout covers both. Allow 8 minutes.
      timeout: 480_000,
    },
  )
  return r.data
}

export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', native: 'English' },
  { code: 'ks', name: 'Kashmiri', native: 'کٲشُر' },
]

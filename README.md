# Zeaniv

> Tell us a sentence about your business. Get back a whole report —
> competitors, trends, ideas worth trying, and a tight summary you can
> hand to anyone. Then listen to it narrated in **Kashmiri**.

This is the hackathon build. It runs locally, end to end, on free
models. The Kashmiri narration is the part we're proudest of and the
part judges should hear with the volume up.

- **Backend:** Django 6 + DRF, Python 3.14, SQLite by default
- **Frontend:** React 18 + Vite + Tailwind v4 + Framer Motion
- **LLMs:** **Ollama** (local Llama / Qwen), **Gemini**, or **Mock** — switch with one env var
- **Translation:** swappable — local Hugging Face model, an external HTTP service, or whichever LLM you've already wired up
- **TTS:** swappable — point at any HTTP TTS server, or load a [Bolbosh / Matcha-TTS](https://github.com/abdulmuizz0903) checkpoint in-process for a Kashmiri voice
- **Async:** Django Q with the ORM broker — no Redis, no extra services

---

## What it does (the 90-second tour)

1. You describe your business in a sentence.
2. Five agents run in order — **competitor → trends → ideation → validation → report**. Each writes to its own table, so the UI can render partial progress while the chain is still running.
3. The session flips to *completed* the moment the report agent finishes. The UI shows the English report.
4. **In the background**, a sixth step kicks in: it translates the executive summary, key insights, and recommended actions to Kashmiri, then synthesises the executive-summary narration with **150 diffusion steps**. Result lands on the Report row.
5. Open the Report tab. Both English and Kashmiri sit side by side. Hit play. The narration is already cached — instant.

Open a previous session and the translation + audio are still there. No re-translate, no re-synthesis. Database-cached on the report.

---

## Read these first if you're judging

- **[docs/the-kashmiri-part.md](docs/the-kashmiri-part.md)** — the unique angle, why it exists, and what's actually hard about it. Start here.
- **[docs/architecture.md](docs/architecture.md)** — pictures. Sequence diagram of the pipeline + localiser, state machine, why we picked each layer.
- **[docs/demo-script.md](docs/demo-script.md)** — the 3-minute walkthrough we'll actually do on stage, with fallback plans if the wifi or TTS server dies.
- **[docs/journal.md](docs/journal.md)** — honest build notes. What surprised us, what we shipped that we'd un-ship, what we ran out of time for.

---

## Quick start

### Prereqs
- Python 3.14 (3.11+ works fine)
- Node 20+ and npm
- Optional: [Ollama](https://ollama.com) running locally if you want a real local LLM. Without it, use `mock` or `gemini`.

### Backend

```bash
# 1. venv
python3 -m venv venv
source venv/bin/activate

# 2. deps
pip install -r requirements.txt

# 3. env
cp .env.example .env
#    LLM_PROVIDER=mock by default — no key needed.
#    Switch to ollama or gemini whenever you're ready.

# 4. db
python manage.py migrate

# 5. go
python manage.py runserver
```

Backend is at <http://localhost:8000>. Sanity check:

```bash
curl http://localhost:8000/healthz/
python scripts/smoke_test.py     # 12-step end-to-end smoke test
```

### Frontend

```bash
cd frontend
cp .env.example .env             # VITE_API_URL=http://localhost:8000
npm install
npm run dev                      # http://localhost:5173
```

Visit <http://localhost:5173>. Click **Try it on yours**, fill in the
form (or pick a saved profile from the popover top-right), choose a
model, hit **Start analysis**.

---

## Demoing the Kashmiri narration

The narration is what'll land for the audience. To make it sing:

1. Set `TTS_URL` (or use the local Matcha-TTS path — see below).
2. Run an analysis on **Ollama** so the localiser actually has work to do (mock skips localisation).
3. Open the Report tab as soon as it's ready. The audio shows up automatically once it's been synthesised — no buttons, no waiting on click.
4. While English is loading, the localiser is already running in the background. By the time the panel reads the summary, the audio is usually ready.

If you're using Bolbosh / Matcha-TTS in-process:

```env
TTS_PROVIDER=local_matcha
TTS_LOCAL_CKPT_PATH=/path/to/your/model.ckpt
TTS_LOCAL_BOLBOSH_PATH=/path/to/Bolbosh
TTS_LOCAL_N_TIMESTEPS=20      # the live "click to listen" path; the
                              # auto-pre-warmed narration still uses 150
```

If you've got a TTS server (Modal, FastAPI, anything HTTP):

```env
TTS_PROVIDER=local_http
TTS_URL=https://your-tts-server.example.com/synth
TTS_STEPS_FIELD=n_timesteps   # or whatever JSON key your server expects
```

---

## Switching LLM providers

Edit `LLM_PROVIDER` in `.env`, **or** pick a model per-run from the **New analysis** form (the form value wins).

| Value     | What it does |
|-----------|---|
| `ollama`  | POSTs to `OLLAMA_BASE_URL` (`http://localhost:11434`) using `OLLAMA_MODEL`. Default for serious local work. |
| `gemini`  | Uses the official `google-genai` SDK with `GEMINI_API_KEY`. Free tier is generous. Fast. |
| `mock`    | Returns hardcoded JSON. No network. Great for UI work and when the wifi conference disappears. |

---

## Async or sync?

By default, `USE_DJANGO_Q=False` — the agent pipeline runs **synchronously inside the start request**. The frontend still polls the status endpoint, so the UX is identical, but you don't need a worker process. Ship-ready demo path.

To run agents on a real worker:

```bash
echo "USE_DJANGO_Q=True" >> .env
python manage.py qcluster           # in a second terminal
python manage.py runserver
```

---

## Tests

```bash
pytest                              # ~20 unit tests, ~1.3s
python scripts/smoke_test.py        # end-to-end HTTP via Django test Client
```

---

## API surface

### Auth
- `POST /api/auth/register/` — create user, returns JWT pair
- `POST /api/auth/login/` — JWT obtain
- `POST /api/auth/refresh/` — JWT refresh
- `GET  /api/auth/me/`

### Business profiles
- `GET    /api/businesses/`
- `POST   /api/businesses/`
- `GET    /api/businesses/{id}/`
- `PUT    /api/businesses/{id}/`
- `DELETE /api/businesses/{id}/`

### Analysis sessions
- `GET  /api/analysis/`
- `POST /api/analysis/start/` — kicks off the pipeline
- `GET  /api/analysis/{id}/`
- `GET  /api/analysis/{id}/status/` — lightweight polling
- `POST /api/analysis/{id}/rerun/`

### Module data
- `GET /api/analysis/{id}/competitors/`
- `GET /api/analysis/{id}/trends/`
- `GET /api/analysis/{id}/ideas/`
- `GET /api/analysis/{id}/validation/`
- `GET /api/analysis/{id}/feedback/`
- `GET /api/analysis/{id}/report/`

### Mutations
- `POST  /api/analysis/{id}/feedback/submit/` — paste raw feedback, returns extracted insights inline
- `POST  /api/analysis/{id}/report/export/` — returns a downloadable PDF
- `POST  /api/analysis/{id}/report/translate/` — Kashmiri (cache-first)
- `POST  /api/analysis/{id}/report/audio/` — Kashmiri narration (cache-first)
- `GET   /api/analysis/{id}/report/audio/` — same, cached blob only
- `PATCH /api/ideas/{id}/` — `is_saved`, `user_rating`, `user_notes`

> Auth is `AllowAny` in dev — unauthenticated requests fall back to a `demo` user. Tighten this for production in `config/settings/production.py`.

---

## Project layout

```
.
├── apps/                            # 8 Django apps
│   ├── users/                       # custom User (UUID PK, email unique)
│   ├── business/                    # BusinessProfile
│   ├── analysis/                    # AnalysisSession, LlmLog, pipeline runner
│   ├── competitors/                 # Competitor
│   ├── feedback/                    # FeedbackSubmission + insights
│   ├── ideas/                       # Idea + IdeaValidation
│   ├── trends/                      # Trend
│   └── reports/                     # Report + post-pipeline localisation
│
├── config/
│   └── settings/{base,development}.py
│
├── services/
│   ├── llm/                         # Pluggable LLM clients
│   │   ├── base.py                  # interface + tolerant JSON parser
│   │   ├── mock_client.py
│   │   ├── ollama_client.py
│   │   ├── gemini_client.py
│   │   └── router.py
│   ├── modules/                     # The 6 agents
│   │   ├── base.py                  # Shared run/log/status
│   │   ├── competitor_agent.py
│   │   ├── trend_agent.py
│   │   ├── ideation_agent.py
│   │   ├── validation_agent.py
│   │   ├── report_agent.py
│   │   └── feedback_agent.py
│   ├── translation/                 # llm | huggingface | local_http
│   ├── tts/                         # local_http | local_matcha
│   └── pdf/report_pdf.py            # reportlab PDF
│
├── frontend/                        # React + Vite + Tailwind + Framer Motion
│   └── src/
│       ├── App.jsx
│       ├── api/client.js
│       ├── components/              # Sidebar, PageHeader, Spinner (+Skeleton, Dots)
│       ├── hooks/usePolling.js
│       └── pages/
│           ├── LandingPage.jsx      # Apple-dark single-file landing
│           ├── DashboardPage.jsx
│           ├── NewAnalysisPage.jsx  # Apple-Store-style configurator
│           ├── SessionPage.jsx
│           └── tabs/{Overview,Competitors,Trends,Ideas,Feedback,Report}Tab.jsx
│
├── tests/                           # pytest + pytest-django (~20 tests)
└── scripts/smoke_test.py            # end-to-end HTTP smoke test
```

---

## How the pipeline runs

```
POST /api/analysis/start/
       │
       ▼
AnalysisSession (status=running, module_status={pending}×5)
       │
       ▼
run_analysis_session(session_id)               ← sync, or Django-Q-queued
       │
       ├── CompetitorAgent   → writes Competitor rows
       ├── TrendAgent        → writes Trend rows
       ├── IdeationAgent     → reads competitors+trends, writes Idea rows
       ├── ValidationAgent   → reads ideas, scores them, writes IdeaValidation
       └── ReportAgent       → reads everything, writes Report
       │
       ▼
session.status = completed                     ← UI surfaces the report here
       │
       ▼
generate_localization(report)                  ← still in the same task
       │     translates summary + insights + actions to Kashmiri
       │     synthesises 150-step Kashmiri narration
       │     persists onto the Report row (ks_translation, ks_audio)
       ▼
report.localization_status = completed         ← UI plays the audio
```

If a single agent throws, that module is marked `failed` and the rest keep running. The localiser is best-effort — if it fails, the English report is still good.

---

## Production notes

This is a hackathon build, not a stack to deploy as-is. Before going to prod:

- `DEBUG=False`, real `SECRET_KEY`, locked `ALLOWED_HOSTS`
- Switch `DATABASES` to Postgres via `DATABASE_URL`
- Tighten `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES` back to `IsAuthenticated` and drop the demo-user fallback in `apps/users/utils.py`
- Front the API with gunicorn or uvicorn; serve `frontend/dist/` from a CDN
- Run `qcluster` as its own process for async sessions

---

## Credits

- Kashmiri TTS uses the [Bolbosh](https://github.com/abdulmuizz0903) fork of Matcha-TTS and the [KashmiriNormalizer](https://github.com/abdulmuizz0903/KashmiriNormalizer)
- Translation defaults to the [koshur-kouter-ks-en_v1](https://huggingface.co/Omarrran/koshur-kouter-ks-en_v1) Hugging Face model
- Inter Tight + Noto Nastaliq Urdu via Google Fonts
- Apple's design language for everything else

— Built fast, made to listen.

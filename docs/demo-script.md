# Demo script

Three minutes. Volume up.

## Before you stand up

```bash
# 1. Pull the model you'll demo on
ollama pull qwen2.5:7b           # or whatever fits your laptop's RAM

# 2. Start everything
source venv/bin/activate
python manage.py runserver &
cd frontend && npm run dev &

# 3. Make sure TTS is reachable (whichever path you chose)
curl -X POST $TTS_URL -d '{"text":"sanity"}' -H "Content-Type: application/json"
```

Open <http://localhost:5173>. Stay on the landing page. Don't click
anything yet.

---

## 0:00 — Land it

> "We tried building one of those 'analyse-your-business' AI tools. We
> got distracted halfway and gave it a Kashmiri voice. Stay for that."

Scroll the landing page once, slowly. Let the cards reveal. Stop on the
big **کٲشُر** moment. Don't explain it yet.

## 0:30 — Run it

Click **Try it on yours**. The "Use saved profile" popover is up top —
you've already created a demo profile, so click it and pick.
(Otherwise type a real one. Keep it under 15 seconds.)

Pick **Ollama**. The configurator highlight slides into place.

Hit **Start analysis**.

## 1:00 — While it runs

The pipeline indicator at the top of the session page lights up agent by
agent: `competitor → trends → ideation → validation → report`. Talk
through it:

> "Five agents, in order. Each one writes its own table, so the
> dashboard renders progress as the chain runs — no spinner of
> mystery."

Click each tab as it fills:

- **Competitors** → "Five real rivals, threat-scored."
- **Trends** → "Industry shifts mapped to opportunities."
- **Ideas** → "Ten ideas, each with next steps and risks."
- **Report** → "And a clean executive summary."

(If you're on Ollama, this is ~30-90s. Talk through it, don't apologise
for the wait.)

## 2:00 — The narration

Click into **Report** the moment the session flips to completed.

> "Now — the panel. The summary's already in English. But while you
> were reading, this happened in the background:"

Point to the audio bar. There's a "Preparing کٲشُر narration"
indicator that's already become a play button by the time you finish
the sentence. Click play.

Let it speak. Don't talk over it.

> "We translated the summary to Kashmiri using a local Hugging Face
> model fine-tuned on Koshur. Then a Bolbosh TTS checkpoint synthesised
> the audio in 150 diffusion steps. Both run on this machine. No
> third-party calls, no key. The audio's saved to the database, so when
> you reopen the session" — *click back to dashboard, click the same
> session* — "it's instant."

The play button is right there, no spinner. Hit play again. Same audio,
zero latency.

## 2:45 — The export

Click **Export PDF**. A `zeaniv-report-<business>.pdf` downloads.
Open it briefly so the panel sees it's a real document, not a snapshot.

## 3:00 — Close

> "That's it. Local LLM, local translation, local voice, real document
> at the end. Built in [N] hours. Questions?"

---

## If something breaks mid-demo

| Failure | Recovery |
|---|---|
| Ollama hangs | Switch to **Gemini** or **Mock** mid-session: open New analysis, pick the same profile, hit start. The dashboard shows both runs so you can flip. |
| Audio doesn't load | The `localization_status` field will say `failed` and surface the reason. Pick a previous session — the audio's cached. |
| TTS server is down | Demo with mock — don't pretend the audio works. The pre-recorded sample audio in `docs/sample-narration.wav` is your backup; play it from QuickLook. |
| Wifi dies | Mock + Ollama both work fully offline. Gemini won't. Don't pick Gemini if the conference wifi is sketchy. |

## Things to *not* do

- Don't open DevTools to "show off the network". The panel doesn't care.
- Don't read every score chip on the report page. Pick one.
- Don't apologise for latency. Talk through it.
- Don't click around tabs nervously. Plant yourself, demo deliberately.

## Things to call out if asked

- "Why Kashmiri?" — Underserved language in BI tooling. We had a real
  Kashmiri TTS checkpoint (Bolbosh, by Abdul Muizz) and a real translator
  (koshur-kouter by Omar) lying around. The product doesn't exclude
  other languages — it's an in-process choice in `services/translation/`.
- "How long does TTS take?" — At 150 steps, ~6-12s for a 200-word
  summary on M2 Pro. Lower steps = faster, fuzzier audio. The form
  exposes a knob in `.env` (`TTS_LOCAL_N_TIMESTEPS`).
- "What's the cost per run?" — On Ollama: zero. On Gemini Flash with
  the free tier: still zero, ~12k tokens. Our heaviest run was 28k
  tokens.
- "Can it train on our data?" — No, we don't fine-tune. The agents are
  all prompt-driven and the prompts are in `services/modules/`.

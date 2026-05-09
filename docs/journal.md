# Build journal

Notes from the build, in roughly the order things happened. If you're
a judge wondering why a particular weird decision exists, the answer
is probably here.

---

## Day 1 — picking fights

We started with the spec the brief implied: a SaaS-shaped business-
intelligence tool with five agents. Within an hour the actual fight
became:

- Sync vs queue? **Sync wins for the demo path.** A worker is one more
  thing to start before going on stage. Django Q is wired up but
  defaults off. `USE_DJANGO_Q=False` runs the chain inside the request
  thread; the frontend polls because it doesn't know the difference.

- One LLM or a switcher? **Switcher.** Anthropic was expensive, Gemini
  free tier was generous, Ollama was offline-safe. The whole agent
  layer talks to a `BaseLLMClient` so swapping is `LLM_PROVIDER=…`. The
  frontend exposes the choice per-run on the New Analysis page.

- SQLite or Postgres? **SQLite.** `DATABASE_URL` works either way. We
  never had to think about it.

We pulled Anthropic out late in the build because we kept blowing
through the free tier on iteration. Claude was good. We just couldn't
afford it. Gemini Flash is the demo-ready cloud option now.

---

## Day 2 — the agents

The agent base class did more lifting than expected. Each agent
inherits from `BaseAgent` and only writes:

```python
def build_user_prompt(self) -> str: ...
def parse_and_save(self, payload: dict) -> None: ...
```

Everything else — status transitions, LLM logging, token accounting,
JSON retry logic — lives in the base. This was unfashionable but it
meant adding the FeedbackAgent (the surprise late-add) took ~40 lines
total.

The thing we learned: **always validate the JSON shape inside
`parse_and_save`**. Llama 3.2 will sometimes return a list when you
asked for a dict. We added per-agent shape checks rather than trusting
the parser; the failure mode shifted from "everything looks fine but
no rows wrote" to "you got an explicit error". Better.

---

## Day 3 — the Kashmiri detour

Originally the plan was: ship in English, put i18n on the post-MVP
list. Then someone in the group said "what if it spoke Kashmiri" as a
joke. We checked Hugging Face. Omar Hyder had already shipped a
translator. We checked GitHub. Abdul Muizz had already shipped a TTS
checkpoint. Suddenly the joke was a feature.

This is when the build got fun.

What we got wrong on first attempt:

1. **Tried to use Google Translate.** Sounded like a tourist's
   Romanised Hindi. Discarded.
2. **Tried to fine-tune a TTS in 4 hours.** Did not finish. Used
   Bolbosh.
3. **Tried to render Kashmiri in Inter Tight.** It just rendered as
   boxes. Loaded Noto Nastaliq Urdu via Google Fonts.
4. **Set line-height to 1.4 on the Nastaliq display word.** Lost the
   bottom 20% of the script. Bumped to 1.9 with explicit padding.
5. **Loaded the HF translator while Ollama was running.** OOM. Wrote
   `services/memory.py` to forcibly swap.

The lesson: we lost ~5 hours to issues that were each 1-2 line fixes
in the end, but only after we understood the actual problem. The
Kashmiri-specific bugs felt like project-killers in the moment. They
weren't. Trust the stack trace.

---

## Day 4 — the UI rewrite (×4)

We tried, in order:

1. **Glassmorphism dark.** Original direction. Looked fine, felt
   generic.
2. **Neumorphism.** User said no. Fair — neumorphic data dashboards
   read as "is that a button or not?"
3. **Brutalism.** Lime accent on black, hard offset shadows, the
   works. Polarising. User said no.
4. **3D dimensional.** Multi-layer shadows, gradient surfaces. Closer.
5. **Apple Dark.** Final. Pure black, translucent surfaces, system
   blue. Everything settled.

We then built a single-file `LandingPage.jsx` using framer-motion for
the parallax hero, scroll-driven clip-path text reveals, snap-rail
bento, and a giant **کٲشُر** moment. The whole thing is one file
because we wanted the landing to be a self-contained showcase that
could be lifted into another project.

The animation choreography uses Apple's cubic-bezier `[0.65, 0, 0.35, 1]`
on every transition. It's heavier than the default and it sells the
"premium" feel.

---

## Day 5 — caching the demo

The localiser was slow. Translating the report and synthesising audio
at 150 diffusion steps takes 10-20s. Doing that on every report load
was unworkable.

We added cache columns to the `Report` model:

- `ks_translation` (JSON)
- `ks_audio` (Binary)
- `ks_audio_content_type` (Char)
- `localization_status` (Char)
- `localization_error` (Text)

The first run stamps everything onto the report. Reopening hits the
cache and skips both translation and TTS. The frontend just trusts
`ks_audio_available` and fetches the cached blob.

This is the bit that made the demo feel "instant on the second open"
which, when judged in the same session as a translation/TTS demo
that's blocked the whole time, reads as polish.

---

## Things we shipped that we're proud of

- The pipeline runs sync **but feels async**. The client polls. Same
  UX, no worker required.
- The provider switcher genuinely works. We tested Mock → Ollama →
  Gemini all on the same business profile and got coherent reports.
- The Apple-dark landing reveals on scroll, including in browsers
  without `animation-timeline: view()` support, via an
  IntersectionObserver fallback. Belt and suspenders.
- The PDF export is real. It's not an HTML-print hack. It's reportlab
  rendering proper pages.

## Things we shipped that we'd un-ship in a refactor

- The `Bilingual` component in ReportTab. It hand-rolls a 2-column
  RTL/LTR layout that should probably just be CSS grid with
  `dir="rtl"` on the right cell. It works. It's not pretty.
- We poll `/status/` every 3s instead of using server-sent events. SSE
  would have halved the chatter. Not a hackathon priority.
- `apps/users/utils.py` has a "demo user" fallback. We ran out of time
  to wire up the proper auth flow. There's a `# TODO: remove this in
  prod` comment that we hope is the kind of comment that doesn't outlive
  us.
- The agent prompts are hardcoded inside `services/modules/*.py`. They
  should be in their own files (or a YAML) so non-engineers can tweak
  copy without grepping Python.

## Things we wanted to ship but ran out of time

- A "regenerate this section" inline button on the report.
- The Trend agent should hit pytrends + NewsAPI for grounding. Right
  now it's purely LLM-derived.
- An "explain this idea in Kashmiri" mic on each idea card.
- Sharded sessions: one user, multiple businesses, side-by-side compare.
- Live transcription overlay during audio playback.

---

## Stuff that was just funny

- The Apple Bezier `[0.65, 0, 0.35, 1]` is in three files. We tried to
  factor it out. We got bored.
- The `n_timesteps` knob is one of those things where 10 sounds bad,
  20 sounds fine, 80 sounds great, 150 is overkill, 1500 is showing
  off, and the difference is mostly inaudible past 80. We use 150 in
  the demo specifically because it's not 80.
- The first version of the bento grid had every card span 2 columns.
  It was a single column. We didn't notice for 3 hours.
- The localiser writes raw audio bytes into a SQLite `BinaryField`.
  This is, technically, a war crime. It works fine.
- The favicon is still a blue circle. We forgot.

---

## Honest acknowledgments

- The `qwen2.5:7b` model on Ollama gave the cleanest agent JSON of
  anything we tested. Worth a shout.
- DRF's `ModelSerializer` is doing 90% of the API surface. Without it
  we'd have spent the whole hackathon on serializers.
- Tailwind v4 dropping the config file was a quiet productivity win.
  We used arbitrary values everywhere and never opened a config.
- The Nastaliq Urdu font from Google Fonts is the only reason the demo
  looks the way it does.

---

## What we'd tell ourselves on day 1

> Pick the weird feature first. Build the rest around it. Don't bury
> the thing that makes you different on a roadmap slide.

That's it.

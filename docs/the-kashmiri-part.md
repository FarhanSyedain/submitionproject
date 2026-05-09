# The Kashmiri part

This wasn't on the brief. It became the whole point.

## Why bother

There's no shortage of "AI business analyser" demos. Most of them ship
a dashboard, an executive summary in English, and a chat box. The
ones that try to add languages either bolt on Google Translate or
pipe through OpenAI's TTS, and you can hear it — that flat,
American-newscaster sound speaking transliterated Hindi.

Kashmiri (کٲشُر) is a different shape. The script is Perso-Arabic,
written in Nastaliq calligraphy. The descenders sweep below the
baseline. The diacritics stack above. Most TTS pipelines either
mispronounce it or don't even tokenise it correctly.

We had access to two things that fixed both problems:

1. **[koshur-kouter-ks-en_v1](https://huggingface.co/Omarrran/koshur-kouter-ks-en_v1)**
   — a translation model fine-tuned by Omar Hyder for Kashmiri↔English.
2. **[Bolbosh](https://github.com/abdulmuizz0903)** — a Matcha-TTS fork
   trained by Abdul Muizz on Kashmiri voice data, shipped with a
   normaliser that handles the script properly.

So the question stopped being "should we add Kashmiri" and became
"how cleanly can we wire it in."

---

## What "150 diffusion steps" means

Matcha-TTS is a **flow-matching diffusion model**. To generate audio,
it iteratively denoises from a Gaussian prior. The number of steps you
take controls the trade-off:

```
20  steps  → 1.5s for ~30 words. Slightly buzzy. Good for "click to
                                                  play" interactive use.
80  steps  → 4s. Smoother. The default for most demos.
150 steps  → 8-12s. Cleaner consonants, less aliasing on tail vowels.
1500 steps → 80s+. Marginal returns. Mostly to brag.
```

We picked 150 for the auto-pre-warmed narration because:

1. The pipeline already takes 30-90s on Ollama. The TTS finishes during
   the same wall-clock window.
2. The audio is generated **once**, persisted to the DB, and replayed
   from cache forever. So the one-time cost buys lifetime quality.
3. The interactive "tap to listen" path (`POST /report/audio/`) keeps
   `TTS_LOCAL_N_TIMESTEPS=20` for sub-second response.

Two diffusion budgets, same model. Set in `.env`:

```env
TTS_LOCAL_N_TIMESTEPS=20      # the click-to-listen path
                              # 150 is hardcoded for the pre-warm
                              # (apps/reports/localization.py)
```

---

## Where the magic actually lives

Three files. Read them in order.

### `services/translation/hf_transformers_client.py`
Loads the koshur-kouter model. Caches it across requests. Translates
in batches because the report has a summary plus N insights plus M
recommended actions, and we'd rather not pay model-load cost N+M+1
times.

### `apps/reports/localization.py`
The orchestrator. It's deliberately simple:

```python
1. Mark report.localization_status = "running"
2. unload_llm()                     # so HF translator can fit on GPU
3. translate_many(summary + insights + actions)
4. Save to report.ks_translation
5. tts.synthesize(summary, lang="ks", num_steps=150)
6. Save bytes + content_type to report.ks_audio
7. Mark report.localization_status = "completed"
```

If any step throws, the status flips to `failed`, the error is saved
on `report.localization_error`, and the calling pipeline keeps going.
The English report is still good. The Kashmiri side just stays empty.

### `services/tts/local_matcha_client.py`
The in-process path. Loads the Bolbosh checkpoint at first call,
keeps it in memory, hands `BaseTTS.synthesize()` the bytes. The
text → phonemes step uses the
[KashmiriNormalizer](https://github.com/abdulmuizz0903/KashmiriNormalizer)
which handles the Nastaliq → IPA conversion that makes pronunciation
sound right instead of like a robot reading transliterated Urdu.

---

## The cache, in plain English

The first time someone runs an analysis, the localiser does its thing
and writes onto the `Report` row:

| Field | What it stores |
|---|---|
| `ks_translation` (JSONField) | Translated summary + insights + actions |
| `ks_audio_text` (Text) | The exact Kashmiri text that was sent to TTS |
| `ks_audio` (Binary) | The raw WAV bytes |
| `ks_audio_content_type` (Char) | e.g. `audio/wav` |
| `localization_status` (Char) | pending / running / completed / failed |
| `localization_error` (Text) | Whatever blew up, blank otherwise |

When someone reopens the session, the frontend pulls
`report.ks_translation` directly from the report JSON (zero extra API
calls) and fetches the audio blob via `POST /report/audio/`, which is
also a cache hit. **No translation re-runs. No TTS re-runs.**

This is why the demo doesn't get awkward when you click around — the
audio is _just there_, every time.

---

## What surprised us

- **Kashmiri Nastaliq descenders** clip in CSS unless you give the line
  ~2× the line-height you'd think you need. We discovered this by
  watching `کٲشُر` get decapitated mid-demo. Fixed in
  `frontend/src/styles.css` with explicit padding-bottom.

- **The Hugging Face translator and Ollama can't co-exist on the GPU.**
  Both load lazily, both refuse to release weights. We had to write
  `services/memory.py` to forcibly unload one before loading the other.
  Once we did that, the demo ran on a 16GB MacBook Pro without
  swapping.

- **Diffusion-step quality is non-monotonic** at the very low end. At
  10 steps the audio is buzzy. At 12-15 it's _worse_ — there's a weird
  ringing artifact. From ~20 onward it scales smoothly. We have no
  idea why. Don't ship under 20.

- **Browser autoplay rules** mean the auto-loaded narration can't just
  start playing when the report opens. The user has to tap. This is
  probably good — it gives the panel a beat to react before the audio
  rolls.

---

## What we'd add next

- More languages, same pattern. Urdu would be easy (same TTS family,
  similar normaliser).
- Live transcription overlay so the audio is captioned as it plays —
  useful for accessibility, not just panels.
- A "regenerate at 1500 steps" button on the report page for the
  paranoid. The 150-step audio is fine. We just want the option.
- An "explain this in Kashmiri" inline mic on each idea card, so users
  can hear individual ideas not just the summary.

---

## Credit where it's due

- [Abdul Muizz](https://github.com/abdulmuizz0903) — Bolbosh TTS, KashmiriNormalizer
- [Omar Hyder](https://huggingface.co/Omarrran) — koshur-kouter translator
- [Matcha-TTS](https://github.com/shivammehta25/Matcha-TTS) — the flow-matching backbone
- Noto Nastaliq Urdu — the only font that renders the script the way
  it should look

If you take one thing from this project: pick the unfashionable
language. The boring ones already have everything.

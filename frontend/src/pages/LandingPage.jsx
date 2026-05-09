/**
 * Zeaniv — Apple Dark landing page.
 *
 * Single-file component using framer-motion + Tailwind v4. Pure dark mode,
 * cinematic parallax hero, scroll-linked text reveals, glassmorphic bento
 * grid, sticky blurred nav. All easing uses the Apple cubic-bezier.
 */
import { useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  motion,
  useScroll,
  useTransform,
  useMotionValue,
  useSpring,
} from 'framer-motion'

// Apple's signature easing curve — feels heavy and decisive.
const APPLE = [0.65, 0, 0.35, 1]

// Single blue accent — used sparingly: gradient headlines, Nastaliq script,
// the primary CTA, and the "report agent" terminal node in the pipeline.
const BLUE_GRADIENT =
  'linear-gradient(135deg, #64d2ff 0%, #0a84ff 60%, #5e5ce6 100%)'
const BLUE = '#0a84ff'

const NASTALIQ =
  '"Noto Nastaliq Urdu", "Noto Naskh Arabic", "Amiri", "Inter", sans-serif'

const FEATURES = [
  {
    n: '01',
    title: 'See who else is in the room.',
    body: 'Five rivals. What they do well, where they leave gaps.',
    span: 'col-span-2 row-span-2',
  },
  {
    n: '02',
    title: 'Read what your customers actually say.',
    body: 'Paste reviews — pain points, requests, and mood come back sorted.',
    span: 'col-span-2',
  },
  {
    n: '03',
    title: 'Catch the wind a little earlier.',
    body: 'Industry shifts mapped to things you could plausibly do this quarter.',
    span: 'col-span-1',
  },
  {
    n: '04',
    title: 'Ten ideas, written for your business.',
    body: 'Not generic — directions worth a real conversation.',
    span: 'col-span-1',
  },
  {
    n: '05',
    title: 'A reality check on each one.',
    body: 'Scored on feasibility, market fit, effort, ROI. Not handwaved.',
    span: 'col-span-2',
  },
  {
    n: '06',
    title: 'Hand someone a real document.',
    body: 'Export a clean PDF. Or play the executive summary back, narrated in Kashmiri.',
    span: 'col-span-4',
  },
]

const PIPELINE = [
  { n: '01', title: 'Business profile', body: 'Your one-line description.', kind: 'input' },
  { n: '02', title: 'Competitor agent', body: 'Scans the field. Five rivals.' },
  { n: '03', title: 'Trend agent', body: 'Maps the shifts moving through your industry.' },
  { n: '04', title: 'Ideation agent', body: 'Writes ten directions, grounded in the findings.' },
  { n: '05', title: 'Validation agent', body: 'Scores each idea on feasibility & ROI.' },
  { n: '06', title: 'Report agent', body: 'Composes the executive summary.', kind: 'output' },
  { n: '∞', title: 'Localization · in the background', body: 'Translates to Kashmiri + 150-step audio.', kind: 'background' },
]

export default function LandingPage() {
  return (
    <div className="bg-black text-[#f5f5f7] min-h-screen overflow-x-clip">
      <Nav />
      <Hero />
      <BentoSection />
      <KashmiriSection />
      <PipelineSection />
      <CTA />
      <Footer />
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Sticky blurred nav
   ───────────────────────────────────────────────────────────────────── */
function Nav() {
  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: APPLE }}
      className="fixed inset-x-0 top-0 z-50 backdrop-blur-md"
      style={{ background: '#00000080', borderBottom: '1px solid rgba(255,255,255,0.06)' }}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3.5">
        <Link to="/" className="flex items-center gap-2">
          <span
            className="grid h-6 w-6 place-items-center rounded-md text-[11px] font-bold text-black"
            style={{ background: 'linear-gradient(160deg,#fff,#a1a1a6)' }}
          >
            Z
          </span>
          <span className="text-[15px] font-semibold tracking-tight">Zeaniv</span>
        </Link>
        <div className="flex items-center gap-7 text-[13px] text-[#a1a1a6]">
          <a href="#features" className="hover:text-white transition-colors duration-200">Features</a>
          <a href="#pipeline" className="hover:text-white transition-colors duration-200">Pipeline</a>
          <Link to="/dashboard" className="hover:text-white transition-colors duration-200">Dashboard</Link>
          <Link
            to="/analyze/new"
            className="rounded-full px-4 py-1.5 text-white backdrop-blur transition-all duration-200 hover:scale-[1.02]"
            style={{
              background: BLUE_GRADIENT,
              boxShadow: '0 0 20px -6px rgba(10,132,255,0.55)',
            }}
          >
            Try it
          </Link>
        </div>
      </div>
    </motion.nav>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Hero — 3D parallax product preview + clip-path-revealed headline
   ───────────────────────────────────────────────────────────────────── */
function Hero() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start start', 'end start'],
  })
  const scale = useTransform(scrollYProgress, [0, 0.5], [1.2, 1])
  const opacity = useTransform(scrollYProgress, [0, 0.55, 0.85], [1, 1, 0])
  const y = useTransform(scrollYProgress, [0, 0.6], [0, -80])

  // Mouse-tracked tilt — the product card tips toward the cursor.
  const mx = useMotionValue(0)
  const my = useMotionValue(0)
  const rotateX = useSpring(useTransform(my, [-300, 300], [10, -10]), {
    stiffness: 120,
    damping: 18,
  })
  const rotateY = useSpring(useTransform(mx, [-300, 300], [-10, 10]), {
    stiffness: 120,
    damping: 18,
  })

  const handleMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect()
    mx.set(e.clientX - r.left - r.width / 2)
    my.set(e.clientY - r.top - r.height / 2)
  }
  const handleLeave = () => {
    mx.set(0)
    my.set(0)
  }

  return (
    <section
      ref={ref}
      className="relative flex min-h-[110vh] items-center justify-center overflow-hidden pt-32 pb-20"
    >
      {/* Soft directional glow behind the hero — adds depth, no color */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse at 50% 0%, rgba(255,255,255,0.04), transparent 50%)',
        }}
      />

      <div className="relative mx-auto flex w-full max-w-6xl flex-col items-center px-6 text-center">
        <motion.span
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: APPLE, delay: 0.1 }}
          className="rounded-full px-3 py-1 text-[12px] font-medium text-[#a1a1a6]"
          style={{ border: '1px solid rgba(255,255,255,0.1)' }}
        >
          Hackathon build · v0.1
        </motion.span>

        {/* Headline · clip-path reveal from center, gradient text mask */}
        <ClipReveal as="h1" className="mt-6 max-w-5xl text-5xl font-semibold leading-[1.02] tracking-tighter md:text-7xl lg:text-[88px]">
          A sentence about your business.
        </ClipReveal>
        <ClipReveal
          as="h1"
          delay={0.15}
          className="mt-2 max-w-5xl text-5xl font-semibold leading-[1.02] tracking-tighter md:text-7xl lg:text-[88px]"
          gradient={BLUE_GRADIENT}
        >
          A whole report back.
        </ClipReveal>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.9, ease: APPLE, delay: 0.4 }}
          className="mt-6 max-w-xl text-[17px] leading-relaxed text-[#a1a1a6]"
        >
          Drop in a one-liner. We'll come back with what your competitors are
          up to, where the market's heading, ideas worth trying, and a clean
          summary you can hand to anyone.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.9, ease: APPLE, delay: 0.55 }}
          className="mt-8 flex flex-wrap justify-center gap-3"
        >
          <Link
            to="/analyze/new"
            className="rounded-full px-6 py-3 text-[14px] font-medium text-white transition-transform duration-200 hover:scale-[1.02] active:scale-[0.98]"
            style={{
              background: BLUE_GRADIENT,
              boxShadow:
                '0 8px 24px -6px rgba(10,132,255,0.50), inset 0 1px 0 rgba(255,255,255,0.20)',
            }}
          >
            Try it on yours
          </Link>
          <Link
            to="/dashboard"
            className="rounded-full px-6 py-3 text-[14px] font-medium text-white transition-colors duration-200 hover:bg-white/10"
            style={{ border: '1px solid rgba(255,255,255,0.18)' }}
          >
            Open dashboard
          </Link>
        </motion.div>

        {/* 3D product preview — parallax + mouse tilt */}
        <motion.div
          style={{
            scale,
            opacity,
            y,
            perspective: 1200,
          }}
          className="mt-20 w-full max-w-4xl"
        >
          <motion.div
            onMouseMove={handleMove}
            onMouseLeave={handleLeave}
            style={{
              rotateX,
              rotateY,
              transformStyle: 'preserve-3d',
            }}
            className="relative"
          >
            <ProductPreview />
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}

function ProductPreview() {
  return (
    <div
      className="relative overflow-hidden rounded-[28px]"
      style={{
        background: '#1d1d1f',
        border: '1px solid rgba(255,255,255,0.1)',
        boxShadow:
          '0 60px 120px -20px rgba(0,0,0,0.8), 0 30px 60px -20px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)',
      }}
    >
      {/* Sheen */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse at top right, rgba(255,255,255,0.08), transparent 50%)',
        }}
      />

      {/* Window chrome */}
      <div className="flex items-center gap-2 border-b border-white/[0.06] px-5 py-3.5">
        <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
        <span className="ml-auto text-[11px] tracking-tight text-[#6e6e73]">zeaniv · executive report</span>
      </div>

      {/* Body */}
      <div className="grid grid-cols-3 gap-4 p-6 md:p-8">
        {/* Left column — narrative */}
        <div className="col-span-2 space-y-4">
          <div className="text-[11px] tracking-[0.18em] text-[#6e6e73]">EXECUTIVE SUMMARY</div>
          <div className="space-y-2.5">
            {[100, 96, 92, 78, 88, 65].map((w, i) => (
              <div
                key={i}
                className="h-2 rounded-full"
                style={{
                  width: `${w}%`,
                  background:
                    'linear-gradient(90deg, rgba(255,255,255,0.18), rgba(255,255,255,0.06))',
                }}
              />
            ))}
          </div>

          <div className="mt-6 text-[11px] tracking-[0.18em] text-[#6e6e73]">KEY INSIGHTS</div>
          <div className="space-y-2">
            {['Distribution channel underused.', 'Competitor pricing soft on tier 2.', 'Tailwind: AI-native procurement tools.'].map((line, i) => (
              <div key={i} className="flex items-center gap-2.5 text-[12.5px] text-[#d1d1d6]">
                <span className="h-1 w-1 rounded-full bg-white/60" />
                <span>{line}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right column — score chips */}
        <div className="space-y-3">
          {[
            { label: 'Feasibility', score: 8.4, accent: true },
            { label: 'Market fit', score: 7.9 },
            { label: 'Effort', score: 5.2 },
            { label: 'ROI', score: 8.1, accent: true },
          ].map((s) => (
            <div
              key={s.label}
              className="rounded-xl p-3"
              style={{
                background: s.accent
                  ? 'rgba(10,132,255,0.06)'
                  : 'rgba(255,255,255,0.04)',
                border: s.accent
                  ? '1px solid rgba(10,132,255,0.20)'
                  : '1px solid rgba(255,255,255,0.06)',
              }}
            >
              <div className="text-[10px] uppercase tracking-wider text-[#6e6e73]">{s.label}</div>
              <div
                className="mt-1 text-2xl font-semibold tracking-tight"
                style={{ color: s.accent ? '#64d2ff' : '#fff' }}
              >
                {s.score}
              </div>
              <div className="mt-2 h-1 rounded-full bg-white/[0.08]">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${(s.score / 10) * 100}%`,
                    background: s.accent ? BLUE_GRADIENT : 'rgba(255,255,255,0.8)',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Bento grid — glassmorphic cards with staggered fade-in
   ───────────────────────────────────────────────────────────────────── */
function BentoSection() {
  const container = {
    hidden: {},
    show: {
      transition: { staggerChildren: 0.08, delayChildren: 0.1 },
    },
  }
  const item = {
    hidden: { opacity: 0, y: 24, filter: 'blur(8px)' },
    show: {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      transition: { duration: 0.9, ease: APPLE },
    },
  }

  return (
    <section id="features" className="px-6 py-32 md:py-40">
      <div className="mx-auto max-w-6xl">
        <ClipReveal as="h2" className="text-center text-4xl font-semibold tracking-tighter md:text-6xl">
          Everything it does.
        </ClipReveal>
        <ClipReveal
          as="h2"
          delay={0.1}
          className="text-center text-4xl font-semibold tracking-tighter md:text-6xl"
          gradient={BLUE_GRADIENT}
        >
          One conversation away.
        </ClipReveal>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: '-100px' }}
          className="mt-16 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
          {FEATURES.map((f) => (
            <motion.article
              key={f.n}
              variants={item}
              className={`relative overflow-hidden rounded-3xl p-7 ${f.span} sm:col-span-2 lg:${f.span}`}
              style={{
                background: 'rgba(29, 29, 31, 0.6)',
                backdropFilter: 'saturate(180%) blur(20px)',
                WebkitBackdropFilter: 'saturate(180%) blur(20px)',
                border: '1px solid rgba(255,255,255,0.1)',
                minHeight: f.span.includes('row-span-2') ? '420px' : '220px',
              }}
            >
              <div
                aria-hidden
                className="pointer-events-none absolute -right-20 -top-20 h-48 w-48 rounded-full"
                style={{
                  background:
                    'radial-gradient(circle, rgba(255,255,255,0.06), transparent 60%)',
                }}
              />
              <div className="font-mono text-[11px] tracking-[0.18em] text-[#6e6e73]">{f.n}</div>
              <h3 className="mt-3 text-[22px] font-semibold leading-tight tracking-tight text-[#f5f5f7] md:text-[26px]">
                {f.title}
              </h3>
              <p className="mt-2 text-[14px] leading-relaxed text-[#a1a1a6]">{f.body}</p>
            </motion.article>
          ))}
        </motion.div>
      </div>
    </section>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Kashmiri / TTS section — giant Nastaliq centerpiece
   ───────────────────────────────────────────────────────────────────── */
function KashmiriSection() {
  return (
    <section className="relative px-6 py-32 md:py-44">
      <div className="mx-auto max-w-5xl text-center">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6, ease: APPLE }}
          className="font-mono text-[12px] tracking-[0.22em] text-[#6e6e73]"
        >
          A SMALL GIFT TO THE PANEL
        </motion.div>

        <ClipReveal as="h2" className="mt-6 text-4xl font-semibold tracking-tighter md:text-6xl lg:text-7xl">
          It even speaks
        </ClipReveal>

        <motion.div
          initial={{ opacity: 0, scale: 0.92, filter: 'blur(20px)' }}
          whileInView={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 1.2, ease: APPLE, delay: 0.15 }}
          dir="rtl"
          className="mt-4 leading-[1.7] tracking-tight"
          style={{
            fontFamily: NASTALIQ,
            fontSize: 'clamp(72px, 14vw, 180px)',
            background: BLUE_GRADIENT,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            paddingBottom: '0.4em',
            paddingTop: '0.15em',
            overflow: 'visible',
          }}
        >
          کٲشُر
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.9, ease: APPLE, delay: 0.4 }}
          className="mx-auto mt-6 max-w-2xl text-[17px] leading-relaxed text-[#a1a1a6]"
        >
          Every report ships with a translated executive summary in Kashmiri
          and a real voice narrating it — synthesised with{' '}
          <span
            className="font-mono text-[14px]"
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 6,
              padding: '0 6px',
            }}
          >
            150 diffusion steps
          </span>
          , generated in the background while the English report loads. Open
          the report tab. Hit play.
        </motion.p>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.9, ease: APPLE, delay: 0.55 }}
          className="mx-auto mt-3 max-w-xl text-[14px] leading-relaxed text-[#6e6e73]"
        >
          Translation runs on a local Hugging Face model. TTS runs on your
          machine. No third-party hop, no key required.
        </motion.p>
      </div>
    </section>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Pipeline diagram — vertical, with glassmorphic markers
   ───────────────────────────────────────────────────────────────────── */
function PipelineSection() {
  const item = {
    hidden: { opacity: 0, x: -20, filter: 'blur(6px)' },
    show: {
      opacity: 1,
      x: 0,
      filter: 'blur(0px)',
      transition: { duration: 0.7, ease: APPLE },
    },
  }
  const container = {
    hidden: {},
    show: { transition: { staggerChildren: 0.08, delayChildren: 0.2 } },
  }

  return (
    <section id="pipeline" className="px-6 py-32 md:py-40">
      <div className="mx-auto max-w-3xl">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6, ease: APPLE }}
          className="text-center font-mono text-[12px] tracking-[0.22em] text-[#6e6e73]"
        >
          UNDER THE HOOD
        </motion.div>

        <ClipReveal as="h2" className="mt-6 text-center text-4xl font-semibold tracking-tighter md:text-6xl">
          Six agents.
        </ClipReveal>
        <ClipReveal
          as="h2"
          delay={0.1}
          className="text-center text-4xl font-semibold tracking-tighter md:text-6xl"
          gradient={BLUE_GRADIENT}
        >
          One pipeline.
        </ClipReveal>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.8, ease: APPLE, delay: 0.3 }}
          className="mx-auto mt-6 max-w-xl text-center text-[16px] leading-relaxed text-[#a1a1a6]"
        >
          Each one specialises. They run in order, hand off to the next, and
          the last sits in the background to localise.
        </motion.p>

        <motion.ol
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: '-100px' }}
          className="relative mx-auto mt-16 max-w-xl space-y-1 list-none p-0"
        >
          {/* Vertical rail */}
          <div
            aria-hidden
            className="absolute left-[23px] top-8 bottom-8 w-px"
            style={{
              background:
                'linear-gradient(to bottom, rgba(255,255,255,0.18), rgba(255,255,255,0.05))',
            }}
          />

          {PIPELINE.map((step) => (
            <motion.li
              key={step.n}
              variants={item}
              className="relative flex items-start gap-5 py-3.5"
            >
              <span
                className="relative z-10 grid h-12 w-12 place-items-center rounded-full"
                style={{
                  background:
                    step.kind === 'output'
                      ? 'rgba(10,132,255,0.15)'
                      : step.kind === 'background'
                      ? 'rgba(255,255,255,0.04)'
                      : '#000',
                  border:
                    step.kind === 'background'
                      ? '1.5px dashed rgba(255,255,255,0.25)'
                      : step.kind === 'output'
                      ? '1.5px solid rgba(10,132,255,0.65)'
                      : '1.5px solid rgba(255,255,255,0.18)',
                  boxShadow:
                    step.kind === 'output'
                      ? '0 0 0 6px #000, 0 0 30px rgba(10,132,255,0.40)'
                      : '0 0 0 6px #000',
                }}
              >
                <span
                  className="font-mono text-[11px] font-semibold"
                  style={{
                    color:
                      step.kind === 'output' ? '#64d2ff' : '#f5f5f7',
                  }}
                >
                  {step.n}
                </span>
              </span>
              <div className="pt-2.5">
                <h4
                  className="text-[17px] font-semibold leading-tight tracking-tight"
                  style={{ color: step.kind === 'background' ? '#a1a1a6' : '#f5f5f7' }}
                >
                  {step.title}
                </h4>
                <p className="mt-1 text-[14px] leading-relaxed text-[#a1a1a6]">{step.body}</p>
              </div>
            </motion.li>
          ))}
        </motion.ol>
      </div>
    </section>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   Closing CTA
   ───────────────────────────────────────────────────────────────────── */
function CTA() {
  return (
    <section className="px-6 py-32 md:py-44">
      <div className="mx-auto max-w-4xl text-center">
        <ClipReveal as="h2" className="text-5xl font-semibold leading-[1.05] tracking-tighter md:text-7xl">
          <span
            style={{
              background: 'linear-gradient(180deg, #f5f5f7 0%, #a1a1a6 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Now then.
          </span>
        </ClipReveal>
        <ClipReveal
          as="h2"
          delay={0.1}
          className="text-5xl font-semibold leading-[1.05] tracking-tighter md:text-7xl"
        >
          What does your business do?
        </ClipReveal>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.9, ease: APPLE, delay: 0.4 }}
          className="mt-12 flex flex-wrap justify-center gap-3"
        >
          <Link
            to="/analyze/new"
            className="rounded-full px-7 py-3.5 text-[15px] font-medium text-white transition-transform duration-200 hover:scale-[1.02] active:scale-[0.98]"
            style={{
              background: BLUE_GRADIENT,
              boxShadow:
                '0 12px 32px -8px rgba(10,132,255,0.55), inset 0 1px 0 rgba(255,255,255,0.22)',
            }}
          >
            Start an analysis
          </Link>
          <Link
            to="/dashboard"
            className="rounded-full px-7 py-3.5 text-[15px] font-medium text-white transition-colors duration-200 hover:bg-white/10"
            style={{ border: '1px solid rgba(255,255,255,0.18)' }}
          >
            See past sessions
          </Link>
        </motion.div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer
      className="px-6 py-10"
      style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
    >
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 text-[12px] text-[#6e6e73]">
        <span>Zeaniv · Hackathon build · v0.1</span>
        <span>Local LLM · Local TTS · Yours to keep.</span>
      </div>
    </footer>
  )
}

/* ─────────────────────────────────────────────────────────────────────
   ClipReveal — scroll-linked text mask. The element starts with
   `clip-path: inset(0 50% 0 50%)` (zero-width sliver in the middle)
   and animates to `inset(0 0 0 0)` as it enters the viewport, revealing
   the text outward from center. Uses the Apple cubic-bezier.
   ───────────────────────────────────────────────────────────────────── */
function ClipReveal({
  as = 'div',
  className = '',
  children,
  delay = 0,
  gradient,
}) {
  const Tag = motion[as] || motion.div
  return (
    <Tag
      initial={{ clipPath: 'inset(0 50% 0 50%)', opacity: 0 }}
      whileInView={{ clipPath: 'inset(0 0% 0 0%)', opacity: 1 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 1.2, ease: APPLE, delay }}
      className={className}
      style={
        gradient
          ? {
              background: gradient,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }
          : undefined
      }
    >
      {children}
    </Tag>
  )
}

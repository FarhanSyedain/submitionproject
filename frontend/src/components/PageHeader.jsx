/**
 * Page header — Apple's hero-on-secondary-page typography.
 * Big tight-tracked title, generous subtitle, breathing room.
 */
export default function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0 flex-1">
        <h1
          className="text-3xl font-semibold leading-tight md:text-4xl"
          style={{ letterSpacing: '-0.035em' }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            className="mt-2 text-[15px] leading-relaxed muted"
            style={{ letterSpacing: '-0.005em' }}
          >
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}

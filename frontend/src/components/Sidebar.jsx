import { NavLink, Link } from 'react-router-dom'

const APPLE_BLUE_GRAD =
  'linear-gradient(135deg, #64d2ff 0%, #0a84ff 60%, #5e5ce6 100%)'

/**
 * Sticky translucent sidebar — iOS / macOS sidebar feel.
 * Blurred surface, hairline divider on the right, generous padding.
 */
export default function Sidebar() {
  return (
    <aside
      className="sticky top-0 hidden h-screen w-64 flex-shrink-0 px-5 py-6 md:block"
      style={{
        background: 'rgba(0, 0, 0, 0.55)',
        backdropFilter: 'saturate(180%) blur(20px)',
        WebkitBackdropFilter: 'saturate(180%) blur(20px)',
        borderRight: '1px solid rgba(255, 255, 255, 0.06)',
      }}
    >
      <Link
        to="/"
        className="mb-10 flex items-center gap-3"
        title="Back to home"
      >
        <div
          className="flex h-9 w-9 items-center justify-center text-[15px] font-semibold text-white"
          style={{
            background: APPLE_BLUE_GRAD,
            borderRadius: 9,
            letterSpacing: '-0.04em',
            boxShadow:
              '0 6px 16px -4px rgba(10,132,255,0.45), inset 0 1px 0 rgba(255,255,255,0.22)',
          }}
        >
          Z
        </div>
        <div className="leading-tight">
          <div className="text-[15px] font-semibold tracking-tight">
            Zeaniv
          </div>
          <div className="text-[11px] font-medium muted tracking-tight">
            Business Intelligence
          </div>
        </div>
      </Link>

      <nav className="flex flex-col gap-1">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <span>Dashboard</span>
        </NavLink>
        <NavLink
          to="/analyze/new"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <span>New analysis</span>
        </NavLink>
      </nav>

      <div className="mt-10 rounded-2xl p-3 text-[12px] leading-relaxed muted"
        style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
        }}
      >
        Running on the demo user. Configure auth to scope by account.
      </div>
    </aside>
  )
}

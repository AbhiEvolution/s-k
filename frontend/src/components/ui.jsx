import { Link } from 'react-router'
import { humanize } from '../lib/format'

export function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
        <path d="M12 5v14M5 12h14" />
      </svg>
    </span>
  )
}

export function PageHeader({ title, description, actions }) {
  return (
    <div className="page-intro">
      <div>
        <h1 className="page-title">{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}

const BADGE = {
  booked: 'badge-green',
  cancelled: 'badge-gray',
  clinic_admin: 'badge-brand',
  doctor: 'badge-green',
  staff: 'badge-amber',
}

export function StatusBadge({ value }) {
  return <span className={`badge ${BADGE[value] ?? 'badge-gray'} capitalize`}>{humanize(value)}</span>
}

export function Stat({ label, value, hint }) {
  return (
    <div className="stat-card">
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
      {hint && <p className="stat-hint">{hint}</p>}
    </div>
  )
}

export function EmptyState({ title, children, action }) {
  return (
    <div className="empty-state">
      <p className="empty-state-title">{title}</p>
      {children && <p className="empty-state-text">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function Loading({ label = 'Loading...' }) {
  return (
    <div role="status" className="flex items-center gap-3 px-6 py-10 text-sm text-slate-500">
      <div className="spinner" /> {label}
    </div>
  )
}

export function Alert({ children, tone = 'error' }) {
  if (!children) return null
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`feedback-${tone} whitespace-pre-line`}>
      {children}
    </div>
  )
}

/** A card with a titled header, for grouping content on a page. */
export function Section({ title, description, actions, children, padded = false }) {
  return (
    <section className="page-card">
      {(title || actions) && (
        <div className="page-card-header flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="section-title">{title}</h2>
            {description && <p className="page-description mt-1">{description}</p>}
          </div>
          {actions}
        </div>
      )}
      <div className={padded ? 'page-card-body' : undefined}>{children}</div>
    </section>
  )
}

export function BackLink({ to, children }) {
  return (
    <Link to={to} className="link text-sm">
      ← {children}
    </Link>
  )
}

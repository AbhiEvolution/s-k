import { Link } from 'react-router'
import { BrandMark } from './ui'

/** The brand-only header for the signed-out pages (login, register). */
export default function Header() {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <Link to="/login" className="brand" aria-label="MediCare">
          <BrandMark />
          <div>
            <p className="app-brand">MediCare</p>
            <p className="app-brand-subtitle">Clinic Portal</p>
          </div>
        </Link>
      </div>
    </header>
  )
}

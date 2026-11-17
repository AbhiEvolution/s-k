import { NavLink, useNavigate } from 'react-router'
import { useDispatch, useSelector } from 'react-redux'
import { API } from '../api/client'
import { useApp } from '../context/AppContext'
import { clearCredentials } from '../features/auth/authSlice'
import { BrandMark } from './ui'

const linkClass = ({ isActive }) => `nav-link${isActive ? ' active' : ''}`

export default function AppHeader() {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const refreshToken = useSelector((state) => state.auth.refreshToken)
  const { role, clinics, clinicId, selectClinic } = useApp()

  const logout = () => {
    // Revoke the session on the server (fire and forget), then forget it locally.
    if (refreshToken) {
      fetch(`${API}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      }).catch(() => {})
    }
    dispatch(clearCredentials())
    navigate('/login', { replace: true })
  }

  return (
    <header className="app-header">
      <div className="app-header-inner">
        <NavLink to="/dashboard" className="brand" aria-label="MediCare home">
          <BrandMark />
          <div>
            <p className="app-brand">MediCare</p>
            <p className="app-brand-subtitle">Clinic Portal</p>
          </div>
        </NavLink>

        <nav aria-label="Main" className="app-nav">
          <NavLink to="/dashboard" className={linkClass}>Dashboard</NavLink>
          <NavLink to="/patients" className={linkClass}>Patients</NavLink>
          <NavLink to="/appointments" className={linkClass}>Appointments</NavLink>
          {role === 'doctor' && <NavLink to="/availability" className={linkClass}>My hours</NavLink>}
          <NavLink to="/clinics" className={linkClass}>Clinics</NavLink>
        </nav>

        <div className="header-actions">
          {clinics.length > 1 && (
            <select
              aria-label="Active clinic"
              value={clinicId ?? ''}
              onChange={(event) => selectClinic(Number(event.target.value))}
              className="clinic-switch"
            >
              {clinics.map((clinic) => (
                <option key={clinic.id} value={clinic.id}>{clinic.name}</option>
              ))}
            </select>
          )}
          {role && <span className="badge badge-brand capitalize">{role}</span>}
          <button type="button" onClick={logout} aria-label="Log out" className="button-secondary button-sm">
            Log out
          </button>
        </div>
      </div>
    </header>
  )
}

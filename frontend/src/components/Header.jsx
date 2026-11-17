
import { useNavigate } from 'react-router'
import { useDispatch, useSelector } from 'react-redux'
import { clearCredentials } from '../features/auth/authSlice'
import { API } from '../api/client'

export default function Header({ showLogout = true }) {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const refreshToken = useSelector((state) => state.auth.refreshToken)

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
        <div>
          <p className="app-brand">MediCare</p>
          <p className="app-brand-subtitle">Doctor Portal</p>
        </div>

        {showLogout && (
          <button
            type="button"
            onClick={logout}
            aria-label="Log out"
            className="button-secondary"
          >
            Logout
          </button>
        )}
      </div>
    </header>
  )
}

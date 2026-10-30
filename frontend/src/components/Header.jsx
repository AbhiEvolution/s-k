
import { useNavigate } from 'react-router'
import { useDispatch } from 'react-redux'
import { clearCredentials } from '../features/auth/authSlice'

export default function Header({ showLogout = true }) {
  const navigate = useNavigate()
  const dispatch = useDispatch()

  const logout = () => {
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

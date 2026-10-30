
import { useState } from 'react'
import { useDispatch } from 'react-redux'
import { useLocation, useNavigate } from 'react-router'
import { setCredentials } from '../features/auth/authSlice'
import Header from '../components/Header'

export default function Login() {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch(
        `${import.meta.env.VITE_DOCTOR_API_URL}/doctors/login`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: email.trim(),
            password,
          }),
        }
      )

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(
          typeof data?.detail === 'string'
            ? data.detail
            : 'Invalid email or password.'
        )
      }

      if (!data?.access_token) {
        throw new Error('Access token was not returned.')
      }
      dispatch(setCredentials(data))
      const destination = location.state?.from
      navigate(
        destination
          ? `${destination.pathname}${destination.search ?? ''}${destination.hash ?? ''}`
          : '/dashboard',
        { replace: true }
      )
    } catch (err) {
      setError(
        err instanceof TypeError
          ? 'Unable to connect to the server.'
          : err.message
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Header showLogout={false} />
      <main className="auth-page">
        <form onSubmit={handleLogin} className="auth-card">
          <div>
            <h1 className="page-title">Welcome back</h1>
            <p className="page-description">Sign in to manage your patient records.</p>
          </div>

          {location.state?.message && (
            <p role="status" className="feedback-success">
              {location.state.message}
            </p>
          )}

          <div className="field-group">
            <label htmlFor="email" className="field-label">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="doctor@example.com"
              autoComplete="username"
              required
              className="field-control"
            />
          </div>

          <div className="field-group">
            <label htmlFor="password" className="field-label">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              required
              className="field-control"
            />
          </div>

          {error && <p role="alert" className="feedback-error">{error}</p>}

          <button type="submit" disabled={loading} className="button-primary">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

          <p className="text-center text-sm text-slate-600">
            New doctor?{' '}
            <button
              type="button"
              onClick={() => navigate('/register')}
              className="font-semibold text-blue-600 hover:text-blue-700"
            >
              Register
            </button>
          </p>
        </form>
      </main>
    </>
  )
}

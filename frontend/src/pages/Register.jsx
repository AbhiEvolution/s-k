
import { useState } from 'react'
import { useNavigate } from 'react-router'
import Header from '../components/Header'

export default function Register() {
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mobileNumber, setMobileNumber] = useState('')
  const [age, setAge] = useState('')
  const [address, setAddress] = useState('')
  const [gender, setGender] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleRegister = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch(
        `${import.meta.env.VITE_DOCTOR_API_URL}/doctors/register`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: username.trim(),
            email: email.trim(),
            password,
            mobile_number: mobileNumber.trim(),
            age: Number(age),
            address: address.trim(),
            gender,
          }),
        }
      )

      const data = await response.json().catch(() => ({}))
 
      if (!response.ok) {
        const detail = data?.detail

        if (Array.isArray(detail)) {
          const messages = detail.map((err) => {
            const field = err.loc?.at(-1) ?? 'Field'

            if (err.type === 'missing') {
              return `${field.replaceAll('_', ' ')} is required.`
            }

            return err.msg
          })

          throw new Error(messages.join('\n'))
        }

        throw new Error(
          typeof detail === 'string'
            ? detail
            : 'Registration failed. Please check your details.'
        )
      }

      navigate('/login', {
        replace: true,
        state: {
          message: 'Registration successful. Please log in.',
        },
      })
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
        <form onSubmit={handleRegister} className="auth-card">
          <div>
            <h1 className="page-title">Create your account</h1>
            <p className="page-description">
              Register your doctor profile to get started.
            </p>
          </div>

          <div className="field-group">
            <label htmlFor="username" className="field-label">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Enter your name"
              autoComplete="name"
              minLength={3}
              maxLength={100}
              required
              className="field-control"
            />
          </div>

          <div className="field-group">
            <label htmlFor="email" className="field-label">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="doctor@example.com"
              autoComplete="email"
              required
              className="field-control"
            />
          </div>

          <div className="field-group">
            <label htmlFor="password" className="field-label">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              autoComplete="new-password"
              minLength={8}
              maxLength={72}
              required
              className="field-control"
            />
          </div>

          <div className="field-group">
            <label htmlFor="mobile_number" className="field-label">
              Mobile Number
            </label>
            <input
              id="mobile_number"
              type="tel"
              value={mobileNumber}
              onChange={(event) => setMobileNumber(event.target.value)}
              placeholder="9807654321"
              inputMode="tel"
              pattern="[+]?[0-9]{10,15}"
              title="Enter 10 to 15 digits, optionally starting with +."
              required
              className="field-control"
            />
          </div>

          <div className="field-group">
            <label htmlFor="age" className="field-label">
              Age
            </label>
            <input
              id="age"
              type="number"
              min="0"
              max="130"
              value={age}
              onChange={(event) => setAge(event.target.value)}
              placeholder="Enter your age"
              required
              className="field-control"
            />
          </div>

          <div className="field-group">
            <label htmlFor="address" className="field-label">
              Address
            </label>
            <textarea
              id="address"
              value={address}
              onChange={(event) => setAddress(event.target.value)}
              placeholder="Enter your address"
              autoComplete="street-address"
              rows={3}
              maxLength={225}
              required
              className="field-control"
            />
          </div>

          <div className="field-group">
            <label htmlFor="gender" className="field-label">
              Gender
            </label>
            <select
              id="gender"
              value={gender}
              onChange={(event) => setGender(event.target.value)}
              required
              className="field-control"
            >
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </select>
          </div>

          {error && (
            <p role="alert" className="feedback-error">
              {error}
            </p>
          )}

          <button type="submit" disabled={loading} className="button-primary">
            {loading ? 'Registering...' : 'Register'}
          </button>

          <p className="text-center text-sm text-slate-600">
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="font-semibold text-blue-600 hover:text-blue-700"
            >
              Sign in
            </button>
          </p>
        </form>
      </main>
    </>
  )
}

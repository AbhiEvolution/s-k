import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useDispatch, useSelector } from 'react-redux'
import { clearCredentials } from '../../features/auth/authSlice'
import Header from '../../components/Header'

export default function NewPatient() {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const token = useSelector((state) => state.auth.accessToken)

  const [name, setName] = useState('')
  const [age, setAge] = useState('')
  const [address, setAddress] = useState('')
  const [mobileNumber, setMobileNumber] = useState('')
  const [gender, setGender] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handlePatient = async (event) => {
    event.preventDefault()
    setError('')

    if (!token) {
      navigate('/login', { replace: true })
      return
    }

    setLoading(true)

    try {
      const response = await fetch(
        `${import.meta.env.VITE_PATIENT_API_URL}/patients`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: name.trim(),
            age: Number(age),
            address: address.trim(),
            mobile_number: mobileNumber.trim(),
            gender,
          }),
        }
      )

      const data = await response.json().catch(() => ({}))

      if (response.status === 401) {
        dispatch(clearCredentials())
        navigate('/login', { replace: true })
        return
      }

      if (!response.ok) {
        const detail = data.detail

        if (Array.isArray(detail)) {
          throw new Error(
            detail
              .map((item) => {
                const field = item.loc?.at(-1) ?? 'Field'
                return `${String(field).replaceAll('_', ' ')}: ${item.msg}`
              })
              .join('\n')
          )
        }

        throw new Error(
          typeof detail === 'string'
            ? detail
            : 'Failed to create patient. Please check your details.'
        )
      }

      navigate('/dashboard', { replace: true })
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
      <Header />
      <main className="page-main page-main-narrow">
        <section className="page-card">
          <div className="page-card-header">
            <h1 className="page-title">Add new patient</h1>
            <p className="page-description">Enter the patient details below.</p>
          </div>
          <form onSubmit={handlePatient} className="form-stack page-card-body">

          <div className="field-group">
            <label htmlFor="name" className="field-label">
              Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter patient name"
              minLength={3}
              maxLength={100}
              required
              className="field-control"
            />
          </div>

          <div className="field-group">
            <label htmlFor="mobileNumber" className="field-label">
              Mobile Number
            </label>
            <input
              id="mobileNumber"
              type="tel"
              value={mobileNumber}
              onChange={(e) => setMobileNumber(e.target.value)}
              placeholder="Enter mobile number"
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
              min="1"
              max="129"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              placeholder="Enter age"
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
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter address"
              rows={3}
              minLength={3}
              maxLength={255}
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
              onChange={(e) => setGender(e.target.value)}
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
            <p className="feedback-error whitespace-pre-line" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="button-primary w-full"
          >
            {loading ? 'Creating...' : 'Create Patient'}
          </button>

          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="button-secondary w-full"
          >
            Back to Dashboard
          </button>
          </form>
        </section>
      </main>
    </>
  )
}
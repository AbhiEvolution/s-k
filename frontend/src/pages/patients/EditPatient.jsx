
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { useDispatch, useSelector } from 'react-redux'
import { clearCredentials } from '../../features/auth/authSlice'
import Header from '../../components/Header'

export default function EditPatient() {
  const { id } = useParams()
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const token = useSelector((state) => state.auth.accessToken)

  const [patient, setPatient] = useState({
    name: '',
    age: '',
    address: '',
    mobile_number: '',
    gender: '',
  })

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    if (!token) {
      navigate('/login', { replace: true })
      return
    }

    async function loadPatient() {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_PATIENT_API_URL}/patients/${id}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        const data = await response.json().catch(() => ({}))

        if (response.status === 401) {
          dispatch(clearCredentials())
          navigate('/login', { replace: true })
          return
        }

        if (!response.ok) {
          throw new Error(
            typeof data?.detail === 'string'
              ? data.detail
              : 'Failed to load patient.'
          )
        }

        setPatient({
          name: data.name ?? '',
          age: data.age ?? '',
          address: data.address ?? '',
          mobile_number: data.mobile_number ?? '',
          gender: data.gender ?? '',
        })
      } catch (err) {
        setLoadError(
          err instanceof TypeError
            ? 'Unable to connect to the server.'
            : err.message
        )
      } finally {
        setLoading(false)
      }
    }

    loadPatient()
  }, [id, token, dispatch, navigate])

  const handleChange = (event) => {
    const { name, value } = event.target
    setPatient((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')

    try {
      const response = await fetch(
        `${import.meta.env.VITE_PATIENT_API_URL}/patients/${id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            ...patient,
            age: Number(patient.age),
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
        const detail = data?.detail
        const message = Array.isArray(detail)
          ? detail
              .map((item) => {
                const field = item.loc?.at(-1) ?? 'Field'
                return `${String(field).replaceAll('_', ' ')}: ${item.msg}`
              })
              .join('\n')
          : typeof detail === 'string'
            ? detail
            : 'Failed to update patient.'
        throw new Error(message)
      }

      navigate('/dashboard')
    } catch (err) {
      setError(
        err instanceof TypeError
          ? 'Unable to connect to the server.'
          : err.message
      )
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <>
        <Header />
        <main className="page-main page-main-narrow">
          <section className="page-card">
            <header className="page-card-header">
              <h1 className="page-title">Edit patient</h1>
              <p className="page-description">Update the patient record.</p>
            </header>
            <div className="page-card-body">
              <p role="status" className="page-description">
                Loading patient...
              </p>
            </div>
          </section>
        </main>
      </>
    )
  }

  return (
    <>
      <Header />
      <main className="page-main page-main-narrow">
        <section className="page-card">
          <header className="page-card-header flex items-start justify-between gap-4">
            <div>
              <h1 className="page-title">Edit patient</h1>
              <p className="page-description">Update the patient record.</p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="button-secondary"
            >
              Cancel
            </button>
          </header>

          {loadError ? (
            <div className="page-card-body grid gap-4">
              <p role="alert" className="feedback-error">
                {loadError}
              </p>
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="button-secondary"
              >
                Back to dashboard
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="form-stack page-card-body">
              {[
                { name: 'name', label: 'Name', type: 'text' },
                { name: 'mobile_number', label: 'Mobile Number', type: 'tel' },
                { name: 'age', label: 'Age', type: 'number' },
                { name: 'address', label: 'Address', type: 'text' },
              ].map((field) => (
                <div key={field.name} className="field-group">
                  <label
                    htmlFor={field.name}
                    className="field-label"
                  >
                    {field.label}
                  </label>
                  <input
                    id={field.name}
                    name={field.name}
                    type={field.type}
                    value={patient[field.name]}
                    onChange={handleChange}
                    minLength={
                      field.name === 'name' || field.name === 'address'
                        ? 3
                        : undefined
                    }
                    maxLength={
                      field.name === 'name'
                        ? 100
                        : field.name === 'address'
                          ? 255
                          : undefined
                    }
                    min={field.name === 'age' ? 1 : undefined}
                    max={field.name === 'age' ? 129 : undefined}
                    inputMode={
                      field.name === 'mobile_number' ? 'tel' : undefined
                    }
                    pattern={
                      field.name === 'mobile_number'
                        ? '[+]?[0-9]{10,15}'
                        : undefined
                    }
                    title={
                      field.name === 'mobile_number'
                        ? 'Enter 10 to 15 digits, optionally starting with +.'
                        : undefined
                    }
                    required
                    className="field-control"
                  />
                </div>
              ))}

              <div className="field-group">
                <label
                  htmlFor="gender"
                  className="field-label"
                >
                  Gender
                </label>
                <select
                  id="gender"
                  name="gender"
                  value={patient.gender}
                  onChange={handleChange}
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
                <p
                  role="alert"
                  className="feedback-error whitespace-pre-line"
                >
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={saving}
                className="button-primary w-full"
              >
                {saving ? 'Saving...' : 'Update Patient'}
              </button>
            </form>
          )}
        </section>
      </main>
    </>
  )
}

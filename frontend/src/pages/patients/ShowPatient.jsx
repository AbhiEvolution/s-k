
import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router'
import { useDispatch, useSelector } from 'react-redux'
import { clearCredentials } from '../../features/auth/authSlice'
import Header from '../../components/Header'

export default function ShowPatient() {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const { id } = useParams()
  const token = useSelector((state) => state.auth.accessToken)

  const [patient, setPatient] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchPatient() {
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
          if (cancelled) return
          dispatch(clearCredentials())
          navigate('/login', { replace: true })
          return
        }

        if (!response.ok) {
          throw new Error(
            typeof data?.detail === 'string'
              ? data.detail
              : 'Failed to fetch patient.'
          )
        }

        if (!cancelled) setPatient(data)
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof TypeError
              ? 'Unable to connect to the server.'
              : err.message
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    if (id && token) fetchPatient()

    return () => {
      cancelled = true
    }
  }, [id, token, dispatch, navigate])

  return (
    <>
      <Header />
      <main className="page-main page-main-narrow">
        <section className="page-card">
          <header className="page-card-header flex items-start justify-between gap-4">
            <div>
              <h1 className="page-title">Patient details</h1>
              <p className="page-description">View this patient record.</p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="button-secondary"
            >
              Back to patients
            </button>
          </header>

          <div className="page-card-body grid gap-5">
            {loading ? (
              <p role="status" className="page-description">Loading patient...</p>
            ) : error ? (
              <p role="alert" className="feedback-error">{error}</p>
            ) : patient ? (
              <div className="grid gap-4">
                <Detail label="Name" value={patient.name} />
                <Detail label="Age" value={patient.age} />
                <Detail label="Gender" value={patient.gender?.replaceAll('_', ' ')} />
                <Detail label="Mobile Number" value={patient.mobile_number} />
                <Detail label="Address" value={patient.address} />
                <Link
                  to={`/patients/${patient.id}/edit`}
                  className="button-primary mt-1"
                >
                  Edit patient
                </Link>
              </div>
            ) : (
              <p className="page-description">Patient not found.</p>
            )}
          </div>
        </section>
      </main>
    </>
  )
}

function Detail({ label, value }) {
  return (
    <div className="detail-row">
      <p className="detail-label">{label}</p>
      <p className="detail-value">{value ?? '-'}</p>
    </div>
  )
}

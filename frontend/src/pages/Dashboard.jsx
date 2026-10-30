
import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router'
import { useDispatch, useSelector } from 'react-redux'
import { clearCredentials } from '../features/auth/authSlice'
import Header from '../components/Header'

const DOCTOR_API = import.meta.env.VITE_DOCTOR_API_URL
const PATIENT_API = import.meta.env.VITE_PATIENT_API_URL

export default function Dashboard() {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const token = useSelector((state) => state.auth.accessToken)

  const [doctor, setDoctor] = useState(null)
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    if (!token) {
      navigate('/login', { replace: true })
      return
    }

    async function loadDashboard() {
      try {
        setLoading(true)
        setError('')

        const headers = {
          Authorization: `Bearer ${token}`,
        }

        const [doctorRes, patientsRes] = await Promise.all([
          fetch(`${DOCTOR_API}/doctors/me`, { headers }),
          fetch(`${PATIENT_API}/patients`, { headers }),
        ])

        if (doctorRes.status === 401 || patientsRes.status === 401) {
          dispatch(clearCredentials())
          navigate('/login', { replace: true })
          return
        }

        const [doctorData, patientsData] = await Promise.all([
          doctorRes.json().catch(() => ({})),
          patientsRes.json().catch(() => ({})),
        ])

        if (!doctorRes.ok) {
          throw new Error(
            typeof doctorData?.detail === 'string'
              ? doctorData?.detail
              : 'Failed to load doctor profile.'
          )
        }

        if (!patientsRes.ok) {
          throw new Error(
            typeof patientsData?.detail === 'string'
              ? patientsData?.detail
              : 'Failed to load patients.'
          )
        }

        setDoctor(doctorData)

        const patientList = Array.isArray(patientsData)
          ? patientsData
          : Array.isArray(patientsData?.items)
            ? patientsData.items
            : Array.isArray(patientsData?.patients)
              ? patientsData.patients
              : []

        setPatients(patientList)
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

    loadDashboard()
  }, [token, dispatch, navigate])

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this patient?')) {
      return
    }

    try {
      setDeletingId(id)
      setError('')

      const response = await fetch(`${PATIENT_API}/patients/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.status === 401) {
        dispatch(clearCredentials())
        navigate('/login', { replace: true })
        return
      }

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(
          typeof data?.detail === 'string'
            ? data.detail
            : 'Failed to delete patient.'
        )
      }

      setPatients((prev) =>
        prev.filter((patient) => patient.id !== id)
      )
    } catch (err) {
      setError(
        err instanceof TypeError
          ? 'Unable to connect to the server.'
          : err.message
      )
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <main className="page-main">
          <section className="page-card page-card-body">
            <p role="status" className="page-description">Loading dashboard...</p>
          </section>
        </main>
      </div>
    )
  }

  const doctorName = doctor?.name ?? doctor?.username ?? 'Doctor'

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <Header />
      <main className="page-main grid gap-6">
        {/* Welcome */}
        <section className="page-card flex flex-col justify-between gap-4 p-6 sm:flex-row sm:items-center">
          <div>
            <p className="page-description mt-0">Welcome back</p>
            <h2 className="page-title mt-1">
              Dr. {doctorName}
            </h2>
            <p className="page-description">
              Manage your patient records in one place.
            </p>
          </div>

          <Link
            to="/patient/new"
            className="button-primary"
          >
            + Add Patient
          </Link>
        </section>

        {/* Patient count */}
        <section className="page-card p-5">
          <p className="field-label">
            Total Patients
          </p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {patients.length}
          </p>
        </section>

        {/* Error */}
        {error && (
          <div
            role="alert"
            className="feedback-error"
          >
            {error}
          </div>
        )}

        {/* Patient list */}
        <section className="page-card">
          <div className="page-card-header">
            <h2 className="page-title text-lg">
              My Patients
            </h2>
            <p className="page-description">
              View and manage your patient records.
            </p>
          </div>

          {patients.length === 0 ? (
            <div className="px-5 py-12 text-center">
            <p className="font-semibold text-slate-800">
                No patients found
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Add a patient to get started.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-5 py-3 font-medium">ID</th>
                    <th className="px-5 py-3 font-medium">Name</th>
                    <th className="px-5 py-3 font-medium">Age</th>
                    <th className="px-5 py-3 font-medium">Gender</th>
                    <th className="px-5 py-3 text-right font-semibold">Actions</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {patients.map((patient) => (
                    <tr key={patient.id} className="hover:bg-slate-50">
                      <td className="px-5 py-4">{patient.id}</td>
                      <td className="px-5 py-4 font-medium text-slate-900">
                        {patient.name}
                      </td>
                      <td className="px-5 py-4">
                        {patient.age ?? '-'}
                      </td>
                      <td className="px-5 py-4 capitalize">
                        {patient.gender?.replaceAll('_', ' ') ?? '-'}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-right">
                        <Link
                          to={`/patients/${patient.id}`}
                          className="font-semibold text-blue-700 hover:underline"
                        >
                          View
                        </Link>

                        <Link
                          to={`/patients/${patient.id}/edit`}
                          className="ml-4 font-semibold text-slate-600 hover:text-slate-900 hover:underline"
                        >
                          Edit
                        </Link>

                        <button
                          type="button"
                          onClick={() => handleDelete(patient.id)}
                          disabled={deletingId === patient.id}
                          aria-label={`Delete ${patient.name}`}
                          className="button-danger ml-2 min-h-0 px-2 py-1"
                        >
                          {deletingId === patient.id ? 'Deleting...' : 'Delete'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

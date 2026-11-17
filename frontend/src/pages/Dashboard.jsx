import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router'
import { useDispatch, useSelector } from 'react-redux'
import { clearCredentials, setClinic } from '../features/auth/authSlice'
import { apiFetch } from '../api/client'
import Header from '../components/Header'

const detailOf = (data, fallback) =>
  typeof data?.detail === 'string' ? data.detail : fallback

export default function Dashboard() {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const token = useSelector((state) => state.auth.accessToken)
  const clinicId = useSelector((state) => state.auth.clinicId)

  const [doctor, setDoctor] = useState(null)
  const [clinics, setClinics] = useState([])
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  // 1) Who am I, and which clinics do I belong to?
  useEffect(() => {
    if (!token) {
      navigate('/login', { replace: true })
      return
    }

    let cancelled = false

    async function loadProfileAndClinics() {
      try {
        setLoading(true)
        setError('')

        const [doctorRes, clinicsRes] = await Promise.all([
          apiFetch('/doctors/me'),
          apiFetch('/clinics'),
        ])

        if (doctorRes.status === 401 || clinicsRes.status === 401) {
          dispatch(clearCredentials())
          navigate('/login', { replace: true })
          return
        }

        // A missing profile (404) is not fatal: we just show a generic name.
        if (doctorRes.ok && !cancelled) setDoctor(await doctorRes.json())

        if (!clinicsRes.ok) {
          const data = await clinicsRes.json().catch(() => ({}))
          throw new Error(detailOf(data, 'Failed to load clinics.'))
        }

        const clinicList = await clinicsRes.json()
        if (cancelled) return
        setClinics(clinicList)

        // Keep the remembered clinic only if I still belong to it.
        if (!clinicList.some((clinic) => clinic.id === clinicId)) {
          dispatch(setClinic(clinicList[0]?.id ?? null))
        }
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

    loadProfileAndClinics()
    return () => {
      cancelled = true
    }
    // clinicId is intentionally not a dependency: this effect sets it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, dispatch, navigate])

  // 2) The patients of the selected clinic.
  useEffect(() => {
    if (!clinicId) return

    let cancelled = false

    async function loadPatients() {
      try {
        const response = await apiFetch(`/patients?clinic_id=${clinicId}`)
        const data = await response.json().catch(() => ({}))

        if (response.status === 401) return // apiFetch already cleared the session

        if (!response.ok) {
          throw new Error(detailOf(data, 'Failed to load patients.'))
        }
        if (!cancelled) setPatients(Array.isArray(data) ? data : [])
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof TypeError
              ? 'Unable to connect to the server.'
              : err.message
          )
        }
      }
    }

    loadPatients()
    return () => {
      cancelled = true
    }
  }, [clinicId, token])

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this patient?')) {
      return
    }

    try {
      setDeletingId(id)
      setError('')

      const response = await apiFetch(`/patients/${id}`, { method: 'DELETE' })

      if (response.status === 401) {
        dispatch(clearCredentials())
        navigate('/login', { replace: true })
        return
      }

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(detailOf(data, 'Failed to delete patient.'))
      }

      setPatients((prev) => prev.filter((patient) => patient.id !== id))
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

  const doctorName = doctor?.full_name ?? 'Doctor'
  const hasClinic = clinicId !== null && clinics.some((clinic) => clinic.id === clinicId)
  const shownPatients = hasClinic ? patients : []

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <main className="page-main grid gap-6">
        {/* Welcome */}
        <section className="page-card flex flex-col justify-between gap-4 p-6 sm:flex-row sm:items-center">
          <div>
            <p className="page-description mt-0">Welcome back</p>
            <h2 className="page-title mt-1">Dr. {doctorName}</h2>
            <p className="page-description">
              Manage your clinic&apos;s patient records in one place.
            </p>
          </div>

          {hasClinic && (
            <Link to="/patient/new" className="button-primary">
              + Add Patient
            </Link>
          )}
        </section>

        {/* Clinic */}
        <section className="page-card p-5">
          <p className="field-label">Clinic</p>
          {clinics.length === 0 ? (
            <p className="mt-2 text-sm text-slate-600">
              You are not a member of any clinic yet. Ask a clinic administrator
              to add you before managing patients.
            </p>
          ) : clinics.length === 1 ? (
            <p className="mt-2 text-lg font-semibold text-slate-900">{clinics[0].name}</p>
          ) : (
            <select
              aria-label="Select clinic"
              value={clinicId ?? ''}
              onChange={(event) => dispatch(setClinic(Number(event.target.value)))}
              className="field-control mt-2"
            >
              {clinics.map((clinic) => (
                <option key={clinic.id} value={clinic.id}>
                  {clinic.name}
                </option>
              ))}
            </select>
          )}
        </section>

        {/* Patient count */}
        <section className="page-card p-5">
          <p className="field-label">Total Patients</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{shownPatients.length}</p>
        </section>

        {/* Error */}
        {error && (
          <div role="alert" className="feedback-error">
            {error}
          </div>
        )}

        {/* Patient list */}
        <section className="page-card">
          <div className="page-card-header">
            <h2 className="page-title text-lg">Clinic Patients</h2>
            <p className="page-description">
              View and manage the patient records of the selected clinic.
            </p>
          </div>

          {shownPatients.length === 0 ? (
            <div className="px-5 py-12 text-center">
              <p className="font-semibold text-slate-800">No patients found</p>
              <p className="mt-1 text-sm text-gray-500">
                {hasClinic ? 'Add a patient to get started.' : 'Join a clinic to see patients.'}
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
                  {shownPatients.map((patient) => (
                    <tr key={patient.id} className="hover:bg-slate-50">
                      <td className="px-5 py-4">{patient.id}</td>
                      <td className="px-5 py-4 font-medium text-slate-900">{patient.name}</td>
                      <td className="px-5 py-4">{patient.age ?? '-'}</td>
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

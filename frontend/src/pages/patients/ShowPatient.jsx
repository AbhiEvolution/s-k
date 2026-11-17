import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { apiFetch, errorMessage, networkMessage } from '../../api/client'
import AppointmentsTable from '../../components/AppointmentsTable'
import { Alert, BackLink, EmptyState, Loading, Section } from '../../components/ui'
import { useClinicDirectory } from '../../hooks/useClinicDirectory'
import { humanize } from '../../lib/format'

export default function ShowPatient() {
  const navigate = useNavigate()
  const { id } = useParams()

  const [state, setState] = useState({ id: null, patient: null, error: '' })
  const [history, setHistory] = useState({ id: null, items: [], upcoming: 0, error: '' })
  const [cancellingId, setCancellingId] = useState(null)
  const [actionError, setActionError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const response = await apiFetch(`/patients/${id}`)
        if (response.status === 401) return
        if (!response.ok) throw new Error(await errorMessage(response, 'Failed to fetch the patient.'))
        const patient = await response.json()
        if (!cancelled) setState({ id, patient, error: '' })
      } catch (err) {
        if (!cancelled) setState({ id, patient: null, error: networkMessage(err) })
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [id])

  const patient = state.id === id ? state.patient : null
  const directory = useClinicDirectory(patient?.clinic_id ?? null)

  // The patient's appointment history, once we know which clinic they belong to.
  const clinicId = patient?.clinic_id
  useEffect(() => {
    if (!clinicId) return
    let cancelled = false

    async function loadHistory() {
      try {
        const response = await apiFetch(`/appointments?clinic_id=${clinicId}&patient_id=${id}&limit=100`)
        if (response.status === 401) return
        if (!response.ok) throw new Error(await errorMessage(response, 'Failed to load appointments.'))
        const items = await response.json()
        const now = Date.now()
        const upcoming = items.filter((a) => a.status === 'booked' && new Date(a.starts_at).getTime() > now).length
        if (!cancelled) setHistory({ id, items, upcoming, error: '' })
      } catch (err) {
        if (!cancelled) setHistory({ id, items: [], upcoming: 0, error: networkMessage(err) })
      }
    }

    loadHistory()
    return () => {
      cancelled = true
    }
  }, [clinicId, id])

  const cancel = async (appointment) => {
    if (!window.confirm('Cancel this appointment?')) return
    try {
      setCancellingId(appointment.id)
      setActionError('')
      const response = await apiFetch(`/appointments/${appointment.id}/cancel`, { method: 'POST' })
      if (response.status === 401) return
      if (!response.ok) throw new Error(await errorMessage(response, 'Failed to cancel the appointment.'))
      const updated = await response.json()
      const wasUpcoming = new Date(appointment.starts_at).getTime() > Date.now()
      setHistory((prev) => ({
        ...prev,
        items: prev.items.map((a) => (a.id === updated.id ? updated : a)),
        upcoming: wasUpcoming ? Math.max(0, prev.upcoming - 1) : prev.upcoming,
      }))
    } catch (err) {
      setActionError(networkMessage(err))
    } finally {
      setCancellingId(null)
    }
  }

  const doctorName = (doctorId) => directory.doctors.find((d) => d.id === doctorId)?.full_name ?? `Doctor #${doctorId}`
  const loading = state.id !== id
  const items = history.id === id ? history.items : []

  return (
    <main className="page-main grid gap-6">
      <BackLink to="/patients">All patients</BackLink>

      {loading ? (
        <Section><Loading label="Loading patient..." /></Section>
      ) : state.error ? (
        <Alert>{state.error}</Alert>
      ) : (
        <div className="grid items-start gap-6 lg:grid-cols-[1fr_2fr]">
          <Section
            title={patient.name}
            description={`Patient #${patient.id}`}
            padded
          >
            <div className="grid gap-4">
              <Detail label="Age" value={patient.age} />
              <Detail label="Gender" value={humanize(patient.gender)} />
              <Detail label="Mobile" value={patient.mobile_number} />
              <Detail label="Email" value={patient.email} />
              <Detail label="Address" value={patient.address} />
              <div className="mt-1 grid gap-2">
                <Link to={`/appointments/new?patient=${patient.id}`} className="button-primary">Book appointment</Link>
                <Link to={`/patients/${patient.id}/edit`} className="button-secondary">Edit patient</Link>
              </div>
            </div>
          </Section>

          <Section
            title="Appointment history"
            description={history.id === id ? `${items.length} total, ${history.upcoming} upcoming.` : undefined}
          >
            <Alert>{actionError || (history.id === id ? history.error : '')}</Alert>
            {history.id !== id || directory.loading ? (
              <Loading label="Loading appointments..." />
            ) : items.length === 0 ? (
              <EmptyState
                title="No appointments yet"
                action={<Link to={`/appointments/new?patient=${patient.id}`} className="button-primary">Book the first one</Link>}
              >
                Appointments booked for this patient will be listed here.
              </EmptyState>
            ) : (
              <AppointmentsTable
                items={[...items].sort((a, b) => b.starts_at.localeCompare(a.starts_at))}
                doctorName={doctorName}
                onCancel={cancel}
                cancellingId={cancellingId}
                showPatient={false}
              />
            )}
          </Section>
        </div>
      )}

      {!loading && !state.error && (
        <div>
          <button type="button" onClick={() => navigate('/patients')} className="button-secondary button-sm">
            Back to patients
          </button>
        </div>
      )}
    </main>
  )
}

function Detail({ label, value }) {
  return (
    <div className="detail-row">
      <p className="detail-label">{label}</p>
      <p className="detail-value capitalize">{value ?? '–'}</p>
    </div>
  )
}

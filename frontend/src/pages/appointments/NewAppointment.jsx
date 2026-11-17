import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { useApp } from '../../context/AppContext'
import { apiFetch, errorMessage, networkMessage } from '../../api/client'
import { useClinicDirectory } from '../../hooks/useClinicDirectory'

const newKey = () =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`

const tomorrow = () => new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
const today = () => new Date().toISOString().slice(0, 10)

export default function NewAppointment() {
  const navigate = useNavigate()
  const { clinicId } = useApp()
  const [searchParams] = useSearchParams()
  const directory = useClinicDirectory(clinicId)

  const [patientId, setPatientId] = useState(searchParams.get('patient') ?? '')
  const [doctorId, setDoctorId] = useState('')
  const [day, setDay] = useState(tomorrow)
  const [selected, setSelected] = useState('')
  const [reason, setReason] = useState('')
  const [slotsResult, setSlotsResult] = useState({ key: null, items: [], error: '' })
  const [refreshTick, setRefreshTick] = useState(0)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  // One idempotency key per attempt: a double click or a retried request after a
  // network blip returns the SAME appointment instead of booking twice.
  const keyRef = useRef(newKey())

  const slotsKey = `${doctorId}|${day}|${refreshTick}`

  useEffect(() => {
    if (!doctorId || !day) return
    let cancelled = false

    async function loadSlots() {
      try {
        const response = await apiFetch(`/appointments/slots?doctor_id=${doctorId}&day=${day}`)
        if (response.status === 401) return
        if (!response.ok) throw new Error(await errorMessage(response, 'Failed to load time slots.'))
        const items = await response.json()
        if (!cancelled) setSlotsResult({ key: slotsKey, items, error: '' })
      } catch (err) {
        if (!cancelled) setSlotsResult({ key: slotsKey, items: [], error: networkMessage(err) })
      }
    }

    loadSlots()
    return () => {
      cancelled = true
    }
  }, [doctorId, day, slotsKey])

  const slotsLoaded = slotsResult.key === slotsKey
  const slots = doctorId && slotsLoaded ? slotsResult.items : []

  const pick = (setter) => (event) => {
    setter(event.target.value)
    setSelected('') // a different doctor or day means a different list of slots
    keyRef.current = newKey()
  }

  const submit = async (event) => {
    event.preventDefault()
    setError('')

    if (!selected) {
      setError('Choose a time slot.')
      return
    }

    setSaving(true)
    try {
      const response = await apiFetch('/appointments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': keyRef.current },
        body: JSON.stringify({
          clinic_id: clinicId,
          doctor_id: Number(doctorId),
          patient_id: Number(patientId),
          starts_at: selected,
          reason: reason.trim() || null,
        }),
      })
      if (response.status === 401) return

      if (!response.ok) {
        const message = await errorMessage(response, 'Failed to book the appointment.')
        if (response.status === 409) {
          // Someone got there first. Show fresh availability and let them choose again.
          setSelected('')
          keyRef.current = newKey()
          setRefreshTick((tick) => tick + 1)
        }
        throw new Error(message)
      }

      navigate('/appointments', { replace: true })
    } catch (err) {
      setError(networkMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const time = (iso) => iso.slice(11, 16)

  return (
    <>
      <main className="page-main page-main-narrow">
        <section className="page-card">
          <div className="page-card-header">
            <h1 className="page-title">Book an appointment</h1>
            <p className="page-description">Pick a patient, a doctor and an open time. Times are in UTC.</p>
          </div>

          {!clinicId ? (
            <p className="page-card-body page-description">
              Select a clinic on the <Link to="/dashboard" className="font-semibold text-brand-700 hover:underline">patients page</Link> first.
            </p>
          ) : directory.loading ? (
            <p role="status" className="page-card-body page-description">Loading...</p>
          ) : (
            <form onSubmit={submit} className="form-stack page-card-body">
              {directory.error && (
                <p role="alert" className="feedback-error">{directory.error}</p>
              )}

              <div className="field-group">
                <label htmlFor="patient" className="field-label">Patient</label>
                <select
                  id="patient"
                  value={patientId}
                  onChange={(event) => setPatientId(event.target.value)}
                  required
                  className="field-control"
                >
                  <option value="">Select a patient</option>
                  {directory.patients.map((patient) => (
                    <option key={patient.id} value={patient.id}>{patient.name}</option>
                  ))}
                </select>
                {directory.patients.length === 0 && (
                  <p className="mt-1 text-sm text-slate-500">
                    This clinic has no patients yet. <Link to="/patient/new" className="font-semibold text-brand-700 hover:underline">Add one</Link>.
                  </p>
                )}
              </div>

              <div className="field-group">
                <label htmlFor="doctor" className="field-label">Doctor</label>
                <select
                  id="doctor"
                  value={doctorId}
                  onChange={pick(setDoctorId)}
                  required
                  className="field-control"
                >
                  <option value="">Select a doctor</option>
                  {directory.doctors.map((doctor) => (
                    <option key={doctor.id} value={doctor.id}>
                      {doctor.full_name}{doctor.specialty ? ` — ${doctor.specialty}` : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field-group">
                <label htmlFor="day" className="field-label">Date (UTC)</label>
                <input
                  id="day"
                  type="date"
                  value={day}
                  min={today()}
                  onChange={pick(setDay)}
                  required
                  className="field-control"
                />
              </div>

              {doctorId && (
                <div className="field-group">
                  <p className="field-label">Time</p>
                  {!slotsLoaded ? (
                    <p role="status" className="text-sm text-slate-500">Loading times...</p>
                  ) : slotsResult.error ? (
                    <p role="alert" className="feedback-error">{slotsResult.error}</p>
                  ) : slots.length === 0 ? (
                    <p className="text-sm text-slate-500">This doctor has no working hours on that day.</p>
                  ) : (
                    <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                      {slots.map((slot) => {
                        const chosen = selected === slot.starts_at
                        return (
                          <button
                            key={slot.starts_at}
                            type="button"
                            disabled={!slot.available}
                            aria-pressed={chosen}
                            onClick={() => setSelected(slot.starts_at)}
                            className={`rounded-md border px-2 py-2 text-sm font-medium ${
                              chosen
                                ? 'border-brand-600 bg-brand-600 text-white'
                                : slot.available
                                  ? 'border-slate-300 bg-white text-slate-800 hover:border-brand-500'
                                  : 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400 line-through'
                            }`}
                          >
                            {time(slot.starts_at)}
                          </button>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}

              <div className="field-group">
                <label htmlFor="reason" className="field-label">Reason (optional)</label>
                <input
                  id="reason"
                  type="text"
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  maxLength={255}
                  className="field-control"
                />
              </div>

              {error && (
                <p role="alert" className="feedback-error whitespace-pre-line">{error}</p>
              )}

              <button type="submit" disabled={saving} className="button-primary w-full">
                {saving ? 'Booking...' : 'Book appointment'}
              </button>
              <button
                type="button"
                onClick={() => navigate('/appointments')}
                className="button-secondary w-full"
              >
                Back to appointments
              </button>
            </form>
          )}
        </section>
      </main>
    </>
  )
}

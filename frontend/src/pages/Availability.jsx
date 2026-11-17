import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { apiFetch, errorMessage, networkMessage } from '../api/client'
import { useApp } from '../context/AppContext'

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

let nextId = 1
const withId = (window) => ({ id: nextId++, ...window })
const hhmm = (value) => value.slice(0, 5) // "09:00:00" -> "09:00"

export default function Availability() {
  const { role } = useApp()
  // status: loading | ready | no-profile | no-clinic | error
  const [state, setState] = useState({ status: 'loading', doctor: null, message: '' })
  const [windows, setWindows] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (role !== 'doctor') return // only doctors have working hours
    let cancelled = false

    async function load() {
      try {
        const meRes = await apiFetch('/doctors/me')
        if (meRes.status === 401) return
        if (meRes.status === 404 || meRes.status === 403) {
          if (!cancelled) setState({ status: 'no-profile', doctor: null, message: '' })
          return
        }
        if (!meRes.ok) throw new Error(await errorMessage(meRes, 'Failed to load your profile.'))

        const doctor = await meRes.json()
        if (!doctor.clinic_id) {
          if (!cancelled) setState({ status: 'no-clinic', doctor, message: '' })
          return
        }

        const response = await apiFetch(`/appointments/availability?doctor_id=${doctor.id}`)
        if (response.status === 401) return
        if (!response.ok) throw new Error(await errorMessage(response, 'Failed to load your hours.'))

        const data = await response.json()
        if (cancelled) return
        setWindows(
          data.windows.map((w) =>
            withId({ weekday: w.weekday, start: hhmm(w.start_time), end: hhmm(w.end_time) })
          )
        )
        setState({ status: 'ready', doctor, message: '' })
      } catch (err) {
        if (!cancelled) setState({ status: 'error', doctor: null, message: networkMessage(err) })
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [role])

  const update = (id, patch) => {
    setSaved(false)
    setWindows((prev) => prev.map((w) => (w.id === id ? { ...w, ...patch } : w)))
  }

  const add = () => {
    setSaved(false)
    setWindows((prev) => [...prev, withId({ weekday: 0, start: '09:00', end: '12:00' })])
  }

  const remove = (id) => {
    setSaved(false)
    setWindows((prev) => prev.filter((w) => w.id !== id))
  }

  const save = async (event) => {
    event.preventDefault()
    setError('')
    setSaved(false)

    const bad = windows.find((w) => !w.start || !w.end || w.end <= w.start)
    if (bad) {
      setError('Each window needs a start time and a later end time.')
      return
    }

    setSaving(true)
    try {
      const response = await apiFetch('/appointments/availability', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          windows: windows.map((w) => ({
            weekday: Number(w.weekday),
            start_time: `${w.start}:00`,
            end_time: `${w.end}:00`,
          })),
        }),
      })
      if (response.status === 401) return
      if (!response.ok) throw new Error(await errorMessage(response, 'Failed to save your hours.'))
      setSaved(true)
    } catch (err) {
      setError(networkMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <main className="page-main page-main-narrow">
        <section className="page-card">
          <div className="page-card-header">
            <h1 className="page-title">My working hours</h1>
            <p className="page-description">
              Patients can only be booked inside these windows. Times are in UTC and are
              split into 30-minute slots. Existing appointments are never changed.
            </p>
          </div>

          <div className="page-card-body">
            {role !== 'doctor' && (
              <p className="page-description">Only doctors have working hours to set.</p>
            )}
            {role === 'doctor' && state.status === 'loading' && (
              <p role="status" className="page-description">Loading...</p>
            )}
            {state.status === 'error' && (
              <p role="alert" className="feedback-error">{state.message}</p>
            )}
            {state.status === 'no-profile' && (
              <p className="page-description">
                Only doctors with a profile can set working hours.
              </p>
            )}
            {state.status === 'no-clinic' && (
              <p className="page-description">
                Your doctor profile is not linked to a clinic yet. Ask a clinic administrator
                to add you, then link your profile, before setting working hours.{' '}
                <Link to="/dashboard" className="font-semibold text-brand-700 hover:underline">Back</Link>
              </p>
            )}

            {state.status === 'ready' && (
              <form onSubmit={save} className="form-stack">
                {windows.length === 0 && (
                  <p className="text-sm text-slate-500">
                    No hours set: nobody can book you yet. Add a window below.
                  </p>
                )}

                {windows.map((w) => (
                  <div key={w.id} className="grid grid-cols-[1fr_auto_auto_auto] items-end gap-2">
                    <div className="field-group">
                      <label htmlFor={`day-${w.id}`} className="field-label">Day</label>
                      <select
                        id={`day-${w.id}`}
                        value={w.weekday}
                        onChange={(e) => update(w.id, { weekday: Number(e.target.value) })}
                        className="field-control"
                      >
                        {WEEKDAYS.map((name, index) => (
                          <option key={name} value={index}>{name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="field-group">
                      <label htmlFor={`start-${w.id}`} className="field-label">From</label>
                      <input
                        id={`start-${w.id}`}
                        type="time"
                        step="1800"
                        value={w.start}
                        onChange={(e) => update(w.id, { start: e.target.value })}
                        className="field-control"
                      />
                    </div>
                    <div className="field-group">
                      <label htmlFor={`end-${w.id}`} className="field-label">To</label>
                      <input
                        id={`end-${w.id}`}
                        type="time"
                        step="1800"
                        value={w.end}
                        onChange={(e) => update(w.id, { end: e.target.value })}
                        className="field-control"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => remove(w.id)}
                      aria-label={`Remove ${WEEKDAYS[w.weekday]} window`}
                      className="button-danger min-h-0 px-2 py-2"
                    >
                      Remove
                    </button>
                  </div>
                ))}

                <button type="button" onClick={add} className="button-secondary w-full">
                  + Add a window
                </button>

                {error && (
                  <p role="alert" className="feedback-error whitespace-pre-line">{error}</p>
                )}
                {saved && (
                  <p role="status" className="feedback-success">Working hours saved.</p>
                )}

                <button type="submit" disabled={saving} className="button-primary w-full">
                  {saving ? 'Saving...' : 'Save working hours'}
                </button>
              </form>
            )}
          </div>
        </section>
      </main>
    </>
  )
}

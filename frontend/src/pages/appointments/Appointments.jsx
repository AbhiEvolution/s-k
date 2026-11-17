import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { apiFetch, errorMessage, networkMessage } from '../../api/client'
import AppointmentsTable from '../../components/AppointmentsTable'
import { Alert, EmptyState, Loading, PageHeader, Section } from '../../components/ui'
import { useApp } from '../../context/AppContext'
import { useClinicDirectory } from '../../hooks/useClinicDirectory'

export default function Appointments() {
  const { clinicId, activeClinic } = useApp()
  const directory = useClinicDirectory(clinicId)

  const [showAll, setShowAll] = useState(false)
  const [result, setResult] = useState({ key: null, items: [], error: '' })
  const [cancellingId, setCancellingId] = useState(null)
  const [actionError, setActionError] = useState('')

  const queryKey = `${clinicId}|${showAll}`

  useEffect(() => {
    if (!clinicId) return
    let cancelled = false

    async function load() {
      try {
        const params = new URLSearchParams({ clinic_id: String(clinicId), limit: '100' })
        if (!showAll) {
          // Default view: what is still ahead of us.
          params.set('start_from', new Date().toISOString())
          params.set('status', 'booked')
        }
        const response = await apiFetch(`/appointments?${params}`)
        if (response.status === 401) return // session ended; the route guard redirects
        if (!response.ok) throw new Error(await errorMessage(response, 'Failed to load appointments.'))

        const items = await response.json()
        if (!cancelled) setResult({ key: queryKey, items, error: '' })
      } catch (err) {
        if (!cancelled) setResult({ key: queryKey, items: [], error: networkMessage(err) })
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [clinicId, showAll, queryKey])

  const doctorName = (id) => directory.doctors.find((d) => d.id === id)?.full_name ?? `Doctor #${id}`
  const patientName = (id) => directory.patients.find((p) => p.id === id)?.name ?? `Patient #${id}`

  const loaded = result.key === queryKey && !directory.loading
  const items = result.key === queryKey ? result.items : []

  const cancel = async (appointment) => {
    if (!window.confirm(`Cancel ${patientName(appointment.patient_id)}'s appointment?`)) return

    try {
      setCancellingId(appointment.id)
      setActionError('')
      const response = await apiFetch(`/appointments/${appointment.id}/cancel`, { method: 'POST' })
      if (response.status === 401) return
      if (!response.ok) throw new Error(await errorMessage(response, 'Failed to cancel the appointment.'))

      const updated = await response.json()
      setResult((prev) => ({
        ...prev,
        // In the default view a cancelled appointment simply disappears.
        items: showAll
          ? prev.items.map((a) => (a.id === updated.id ? updated : a))
          : prev.items.filter((a) => a.id !== updated.id),
      }))
    } catch (err) {
      setActionError(networkMessage(err))
    } finally {
      setCancellingId(null)
    }
  }

  return (
    <main className="page-main grid gap-6">
      <PageHeader
        title="Appointments"
        description={`${activeClinic ? `${activeClinic.name}. ` : ''}Times are shown in UTC.`}
        actions={clinicId && <Link to="/appointments/new" className="button-primary">+ Book appointment</Link>}
      />

      {!clinicId ? (
        <Section>
          <EmptyState title="No clinic selected">
            Join a clinic to see its appointments. <Link to="/clinics" className="link">Go to clinics</Link>.
          </EmptyState>
        </Section>
      ) : (
        <>
          <Alert>{actionError || directory.error || (result.key === queryKey ? result.error : '')}</Alert>

          <Section
            title={showAll ? 'All appointments' : 'Upcoming appointments'}
            actions={
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  type="checkbox"
                  checked={showAll}
                  onChange={(event) => setShowAll(event.target.checked)}
                />
                Include past and cancelled
              </label>
            }
          >
            {!loaded ? (
              <Loading label="Loading appointments..." />
            ) : items.length === 0 ? (
              <EmptyState
                title="No appointments"
                action={<Link to="/appointments/new" className="button-primary">Book one</Link>}
              >
                Nothing matches this view yet.
              </EmptyState>
            ) : (
              <AppointmentsTable
                items={items}
                patientName={patientName}
                doctorName={doctorName}
                onCancel={cancel}
                cancellingId={cancellingId}
              />
            )}
          </Section>
        </>
      )}
    </main>
  )
}

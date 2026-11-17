import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { apiFetch, errorMessage, networkMessage } from '../api/client'
import { Alert, EmptyState, Loading, PageHeader, Section, Stat, StatusBadge } from '../components/ui'
import { useApp } from '../context/AppContext'
import { useClinicDirectory } from '../hooks/useClinicDirectory'
import { formatTime, utcDate } from '../lib/format'

const DAY_MS = 24 * 60 * 60 * 1000

function greeting() {
  const hour = new Date().getHours()
  return hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
}

export default function Dashboard() {
  const { clinicId, activeClinic, doctor, role, isAdmin } = useApp()
  const directory = useClinicDirectory(clinicId)
  const [upcoming, setUpcoming] = useState({ clinicId: null, items: [], error: '' })

  // The next seven days of booked appointments, in one request.
  useEffect(() => {
    if (!clinicId) return
    let cancelled = false

    async function load() {
      try {
        const now = new Date()
        const params = new URLSearchParams({
          clinic_id: String(clinicId),
          status: 'booked',
          start_from: now.toISOString(),
          start_to: new Date(now.getTime() + 7 * DAY_MS).toISOString(),
          limit: '100',
        })
        const response = await apiFetch(`/appointments?${params}`)
        if (response.status === 401) return
        if (!response.ok) throw new Error(await errorMessage(response, 'Failed to load appointments.'))
        const items = await response.json()
        if (!cancelled) setUpcoming({ clinicId, items, error: '' })
      } catch (err) {
        if (!cancelled) setUpcoming({ clinicId, items: [], error: networkMessage(err) })
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [clinicId])

  const name = doctor?.full_name ? `Dr. ${doctor.full_name.replace(/^Dr\.?\s*/i, '')}` : null
  const intro = (
    <PageHeader
      title={`${greeting()}${name ? `, ${name}` : ''}`}
      description={activeClinic ? `Here is what is happening at ${activeClinic.name}.` : 'Welcome to MediCare.'}
    />
  )

  if (!clinicId) {
    return (
      <main className="page-main">
        {intro}
        <Section>
          <EmptyState
            title="You are not part of a clinic yet"
            action={isAdmin && <Link to="/clinics" className="button-primary">Create a clinic</Link>}
          >
            {isAdmin
              ? 'Create your first clinic, then add doctors and staff to it.'
              : 'Ask a clinic administrator to add you. Once you are a member, patients and appointments appear here.'}
          </EmptyState>
        </Section>
      </main>
    )
  }

  const loaded = upcoming.clinicId === clinicId && !directory.loading
  const items = upcoming.clinicId === clinicId ? upcoming.items : []
  const today = utcDate()
  const todayCount = items.filter((a) => utcDate(a.starts_at) === today).length
  const mine = doctor ? items.filter((a) => a.doctor_id === doctor.id).length : null
  const patientCount = directory.patients.length
  const nameOf = (list, id, key) => list.find((x) => x.id === id)?.[key]

  const tips = []
  if (role === 'doctor' && !doctor) tips.push('Your doctor profile is missing, so you cannot be booked yet.')
  if (role === 'doctor' && doctor && !doctor.clinic_id) tips.push('Link your doctor profile to a clinic to appear in booking.')

  return (
    <main className="page-main grid gap-6">
      {intro}

      {tips.map((tip) => <Alert key={tip}>{tip}</Alert>)}
      <Alert>{directory.error || upcoming.error}</Alert>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Patients" value={loaded ? (patientCount >= 100 ? '100+' : patientCount) : '–'} hint="in this clinic" />
        <Stat label="Today" value={loaded ? todayCount : '–'} hint="appointments still ahead (UTC)" />
        <Stat
          label="Next 7 days"
          value={loaded ? items.length : '–'}
          hint={mine !== null && loaded ? `${mine} with you` : 'booked appointments'}
        />
        <Stat label="Doctors" value={loaded ? directory.doctors.length : '–'} hint="working at this clinic" />
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-[2fr_1fr]">
        <Section
          title="Coming up"
          description="The next booked appointments."
          actions={<Link to="/appointments" className="link text-sm">View all</Link>}
        >
          {!loaded ? (
            <Loading />
          ) : items.length === 0 ? (
            <EmptyState
              title="Nothing booked this week"
              action={<Link to="/appointments/new" className="button-primary">Book an appointment</Link>}
            >
              Appointments you book will show up here.
            </EmptyState>
          ) : (
            <div>
              {items.slice(0, 6).map((appointment) => {
                const when = new Date(appointment.starts_at)
                const isToday = utcDate(appointment.starts_at) === today
                return (
                  <div key={appointment.id} className="list-row">
                    <div className="flex min-w-0 items-center gap-4">
                      <div className="w-20 shrink-0 text-center">
                        <p className="m-0 text-base font-bold">{formatTime(appointment.starts_at)}</p>
                        <p className="m-0 text-xs text-slate-500">
                          {isToday ? 'Today' : when.toLocaleDateString('en-GB', { timeZone: 'UTC', weekday: 'short', day: 'numeric', month: 'short' })}
                        </p>
                      </div>
                      <div className="min-w-0">
                        <Link to={`/patients/${appointment.patient_id}`} className="link block truncate">
                          {nameOf(directory.patients, appointment.patient_id, 'name') ?? `Patient #${appointment.patient_id}`}
                        </Link>
                        <p className="m-0 truncate text-sm text-slate-500">
                          with {nameOf(directory.doctors, appointment.doctor_id, 'full_name') ?? `doctor #${appointment.doctor_id}`}
                        </p>
                      </div>
                    </div>
                    <StatusBadge value={appointment.status} />
                  </div>
                )
              })}
            </div>
          )}
        </Section>

        <Section title="Quick actions" padded>
          <div className="grid gap-2">
            <Link to="/appointments/new" className="button-primary">Book appointment</Link>
            <Link to="/patient/new" className="button-secondary">Add patient</Link>
            {role === 'doctor' && <Link to="/availability" className="button-secondary">Set my working hours</Link>}
            <Link to="/clinics" className="button-secondary">Manage clinics</Link>
          </div>
        </Section>
      </div>
    </main>
  )
}

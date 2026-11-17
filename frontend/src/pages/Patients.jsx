import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { apiFetch, errorMessage, networkMessage } from '../api/client'
import { Alert, EmptyState, Loading, PageHeader, Section } from '../components/ui'
import { useApp } from '../context/AppContext'
import { humanize } from '../lib/format'

export default function Patients() {
  const { clinicId, activeClinic } = useApp()
  const [result, setResult] = useState({ clinicId: null, items: [], error: '' })
  const [query, setQuery] = useState('')
  const [deletingId, setDeletingId] = useState(null)
  const [actionError, setActionError] = useState('')

  useEffect(() => {
    if (!clinicId) return
    let cancelled = false

    async function load() {
      try {
        const response = await apiFetch(`/patients?clinic_id=${clinicId}`)
        if (response.status === 401) return
        if (!response.ok) throw new Error(await errorMessage(response, 'Failed to load patients.'))
        const items = await response.json()
        if (!cancelled) setResult({ clinicId, items, error: '' })
      } catch (err) {
        if (!cancelled) setResult({ clinicId, items: [], error: networkMessage(err) })
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [clinicId])

  const remove = async (patient) => {
    if (!window.confirm(`Delete ${patient.name}? This cannot be undone.`)) return
    try {
      setDeletingId(patient.id)
      setActionError('')
      const response = await apiFetch(`/patients/${patient.id}`, { method: 'DELETE' })
      if (response.status === 401) return
      if (!response.ok) throw new Error(await errorMessage(response, 'Failed to delete the patient.'))
      setResult((prev) => ({ ...prev, items: prev.items.filter((p) => p.id !== patient.id) }))
    } catch (err) {
      setActionError(networkMessage(err))
    } finally {
      setDeletingId(null)
    }
  }

  const loaded = result.clinicId === clinicId
  const items = loaded ? result.items : []
  const needle = query.trim().toLowerCase()
  const shown = needle
    ? items.filter((p) => `${p.name} ${p.mobile_number ?? ''} ${p.email ?? ''}`.toLowerCase().includes(needle))
    : items

  return (
    <main className="page-main grid gap-6">
      <PageHeader
        title="Patients"
        description={activeClinic ? `Patient records at ${activeClinic.name}.` : 'Patient records.'}
        actions={clinicId && <Link to="/patient/new" className="button-primary">+ Add patient</Link>}
      />

      {!clinicId ? (
        <Section>
          <EmptyState title="No clinic selected">
            Join a clinic to see its patients. <Link to="/clinics" className="link">Go to clinics</Link>.
          </EmptyState>
        </Section>
      ) : (
        <>
          <Alert>{actionError || (loaded ? result.error : '')}</Alert>

          <Section
            title={`${shown.length} ${shown.length === 1 ? 'patient' : 'patients'}`}
            actions={
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search name, phone or email"
                aria-label="Search patients"
                className="field-control max-w-xs"
              />
            }
          >
            {!loaded ? (
              <Loading label="Loading patients..." />
            ) : shown.length === 0 ? (
              <EmptyState
                title={needle ? 'No matches' : 'No patients yet'}
                action={!needle && <Link to="/patient/new" className="button-primary">Add the first patient</Link>}
              >
                {needle ? 'Try a different search.' : 'Add a patient to start booking appointments.'}
              </EmptyState>
            ) : (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Age</th>
                      <th>Gender</th>
                      <th>Contact</th>
                      <th className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shown.map((patient) => (
                      <tr key={patient.id}>
                        <td>
                          <Link to={`/patients/${patient.id}`} className="link">{patient.name}</Link>
                        </td>
                        <td>{patient.age ?? '–'}</td>
                        <td className="capitalize">{humanize(patient.gender) || '–'}</td>
                        <td>
                          <div>{patient.mobile_number}</div>
                          {patient.email && <div className="text-xs text-slate-500">{patient.email}</div>}
                        </td>
                        <td className="whitespace-nowrap text-right">
                          <Link to={`/appointments/new?patient=${patient.id}`} className="link">Book</Link>
                          <Link to={`/patients/${patient.id}/edit`} className="link ml-4 !text-slate-600">Edit</Link>
                          <button
                            type="button"
                            onClick={() => remove(patient)}
                            disabled={deletingId === patient.id}
                            aria-label={`Delete ${patient.name}`}
                            className="button-danger button-sm ml-3"
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
          </Section>
        </>
      )}
    </main>
  )
}

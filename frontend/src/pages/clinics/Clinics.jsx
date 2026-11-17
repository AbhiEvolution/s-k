import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { apiFetch, errorMessage, networkMessage } from '../../api/client'
import { Alert, EmptyState, PageHeader, Section } from '../../components/ui'
import { useApp } from '../../context/AppContext'

export default function Clinics() {
  const navigate = useNavigate()
  const { clinics, clinicId, isAdmin, selectClinic, reload } = useApp()

  const [form, setForm] = useState({ name: '', address: '', phone: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const change = (event) => setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }))

  const create = async (event) => {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      const response = await apiFetch('/clinics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name.trim(),
          address: form.address.trim() || null,
          phone: form.phone.trim() || null,
        }),
      })
      if (response.status === 401) return
      if (!response.ok) throw new Error(await errorMessage(response, 'Failed to create the clinic.'))

      const clinic = await response.json()
      reload() // refresh "my clinics" everywhere
      selectClinic(clinic.id)
      navigate(`/clinics/${clinic.id}`)
    } catch (err) {
      setError(networkMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="page-main grid gap-6">
      <PageHeader
        title="Clinics"
        description="The clinics you belong to. Patients and appointments are always scoped to one clinic."
      />

      <div className="grid items-start gap-6 lg:grid-cols-[2fr_1fr]">
        <Section title="Your clinics">
          {clinics.length === 0 ? (
            <EmptyState title="No clinics yet">
              {isAdmin
                ? 'Create your first clinic with the form, then add your team.'
                : 'Ask a clinic administrator to add you to their clinic.'}
            </EmptyState>
          ) : (
            <div>
              {clinics.map((clinic) => (
                <div key={clinic.id} className="list-row">
                  <div className="min-w-0">
                    <p className="m-0 flex items-center gap-2 font-semibold">
                      <span className="truncate">{clinic.name}</span>
                      {clinic.id === clinicId && <span className="badge badge-brand">Active</span>}
                    </p>
                    <p className="m-0 truncate text-sm text-slate-500">
                      {[clinic.address, clinic.phone].filter(Boolean).join(' · ') || 'No contact details yet'}
                    </p>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    {clinic.id !== clinicId && (
                      <button type="button" onClick={() => selectClinic(clinic.id)} className="button-secondary button-sm">
                        Switch to
                      </button>
                    )}
                    <Link to={`/clinics/${clinic.id}`} className="button-primary button-sm">Manage</Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>

        {isAdmin ? (
          <Section title="New clinic" description="Only administrators can create clinics." padded>
            <form onSubmit={create} className="form-stack">
              <div className="field-group">
                <label htmlFor="clinic-name" className="field-label">Name</label>
                <input
                  id="clinic-name" name="name" value={form.name} onChange={change}
                  minLength={2} maxLength={100} required className="field-control"
                  placeholder="Sunrise Family Clinic"
                />
              </div>
              <div className="field-group">
                <label htmlFor="clinic-address" className="field-label">Address (optional)</label>
                <input
                  id="clinic-address" name="address" value={form.address} onChange={change}
                  maxLength={255} className="field-control"
                />
              </div>
              <div className="field-group">
                <label htmlFor="clinic-phone" className="field-label">Phone (optional)</label>
                <input
                  id="clinic-phone" name="phone" type="tel" value={form.phone} onChange={change}
                  pattern="[+]?[0-9]{10,15}" title="10 to 15 digits, optionally starting with +"
                  className="field-control"
                />
              </div>
              <Alert>{error}</Alert>
              <button type="submit" disabled={saving} className="button-primary">
                {saving ? 'Creating...' : 'Create clinic'}
              </button>
            </form>
          </Section>
        ) : (
          <Section title="Need a new clinic?" padded>
            <p className="page-description mt-0">Clinics are created by platform administrators.</p>
          </Section>
        )}
      </div>
    </main>
  )
}

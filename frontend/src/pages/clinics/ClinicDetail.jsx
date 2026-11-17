import { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import { apiFetch, errorMessage, networkMessage } from '../../api/client'
import { Alert, BackLink, EmptyState, Loading, PageHeader, Section, StatusBadge } from '../../components/ui'
import { useApp } from '../../context/AppContext'

const ROLES = [
  { value: 'doctor', label: 'Doctor' },
  { value: 'staff', label: 'Staff' },
  { value: 'clinic_admin', label: 'Clinic admin' },
]

export default function ClinicDetail() {
  const { id } = useParams()
  const { userId, isAdmin, reload } = useApp()

  const [data, setData] = useState({ id: null, clinic: null, members: [], emails: {}, error: '' })
  const [tick, setTick] = useState(0)
  const refresh = () => setTick((value) => value + 1)

  const [details, setDetails] = useState(null) // edit form, seeded once the clinic loads
  const [member, setMember] = useState({ who: '', role: 'doctor' })
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [clinicRes, membersRes] = await Promise.all([
          apiFetch(`/clinics/${id}`),
          apiFetch(`/clinics/${id}/members`),
        ])
        if (clinicRes.status === 401 || membersRes.status === 401) return
        if (!clinicRes.ok) throw new Error(await errorMessage(clinicRes, 'Clinic not found.'))
        if (!membersRes.ok) throw new Error(await errorMessage(membersRes, 'Failed to load members.'))

        const [clinic, members] = await Promise.all([clinicRes.json(), membersRes.json()])

        // Only platform admins may look accounts up. Everyone else sees user ids.
        let emails = {}
        if (isAdmin && members.length > 0) {
          const lookup = await apiFetch(`/auth/users?ids=${members.map((m) => m.user_id).join(',')}`)
          if (lookup.ok) {
            emails = Object.fromEntries((await lookup.json()).map((user) => [user.id, user.email]))
          }
        }

        if (cancelled) return
        setData({ id, clinic, members, emails, error: '' })
        setDetails((prev) => prev ?? { name: clinic.name, address: clinic.address ?? '', phone: clinic.phone ?? '' })
      } catch (err) {
        if (!cancelled) setData({ id, clinic: null, members: [], emails: {}, error: networkMessage(err) })
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [id, tick, isAdmin])

  const loading = data.id !== id
  const { clinic, members, emails } = data
  const mine = members.find((m) => m.user_id === userId)
  const canManage = mine?.role === 'clinic_admin'

  const run = async (label, work) => {
    setBusy(label)
    setError('')
    setNotice('')
    try {
      await work()
    } catch (err) {
      setError(networkMessage(err))
    } finally {
      setBusy('')
    }
  }

  const saveDetails = (event) => {
    event.preventDefault()
    return run('details', async () => {
      const response = await apiFetch(`/clinics/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: details.name.trim(),
          address: details.address.trim() || null,
          phone: details.phone.trim() || null,
        }),
      })
      if (response.status === 401) return
      if (!response.ok) throw new Error(await errorMessage(response, 'Failed to save the clinic.'))
      setNotice('Clinic details saved.')
      reload() // the header's clinic list shows the new name
      refresh()
    })
  }

  const addMember = (event) => {
    event.preventDefault()
    return run('add', async () => {
      const who = member.who.trim()
      let newUserId

      if (who.includes('@')) {
        if (!isAdmin) {
          throw new Error('Only platform administrators can look people up by email. Ask the person for their user ID instead.')
        }
        const lookup = await apiFetch(`/auth/users?email=${encodeURIComponent(who)}`)
        if (!lookup.ok) throw new Error(await errorMessage(lookup, 'Lookup failed.'))
        const [user] = await lookup.json()
        if (!user) throw new Error('No account with that email address.')
        newUserId = user.id
      } else if (/^\d+$/.test(who)) {
        newUserId = Number(who)
      } else {
        throw new Error('Enter an email address or a numeric user ID.')
      }

      const response = await apiFetch(`/clinics/${id}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: newUserId, role: member.role }),
      })
      if (response.status === 401) return
      if (!response.ok) throw new Error(await errorMessage(response, 'Failed to add the member.'))

      setMember((prev) => ({ ...prev, who: '' }))
      setNotice('Member added.')
      refresh()
    })
  }

  const removeMember = (target) => {
    const label = emails[target.user_id] ?? `user #${target.user_id}`
    if (!window.confirm(`Remove ${label} from this clinic?`)) return
    return run(`remove-${target.user_id}`, async () => {
      const response = await apiFetch(`/clinics/${id}/members/${target.user_id}`, { method: 'DELETE' })
      if (response.status === 401) return
      if (!response.ok) throw new Error(await errorMessage(response, 'Failed to remove the member.'))
      setNotice('Member removed.')
      refresh()
    })
  }

  const setField = (event) => setDetails((prev) => ({ ...prev, [event.target.name]: event.target.value }))

  return (
    <main className="page-main grid gap-6">
      <BackLink to="/clinics">All clinics</BackLink>

      {loading ? (
        <Section><Loading label="Loading clinic..." /></Section>
      ) : data.error ? (
        <Alert>{data.error}</Alert>
      ) : (
        <>
          <PageHeader
            title={clinic.name}
            description={
              canManage
                ? 'You administer this clinic.'
                : mine
                  ? `You are a ${mine.role.replace('_', ' ')} here.`
                  : undefined
            }
          />

          <Alert>{error}</Alert>
          <Alert tone="success">{notice}</Alert>

          <div className="grid items-start gap-6 lg:grid-cols-[3fr_2fr]">
            <Section title={`Members (${members.length})`} description="Who can work with this clinic's patients and appointments.">
              {members.length === 0 ? (
                <EmptyState title="No members" />
              ) : (
                <div>
                  {members.map((m) => (
                    <div key={m.user_id} className="list-row">
                      <div className="min-w-0">
                        <p className="m-0 truncate font-semibold">
                          {emails[m.user_id] ?? `User #${m.user_id}`}
                          {m.user_id === userId && <span className="ml-2 text-xs font-normal text-slate-500">(you)</span>}
                        </p>
                        {emails[m.user_id] && <p className="m-0 text-xs text-slate-500">User #{m.user_id}</p>}
                      </div>
                      <div className="flex shrink-0 items-center gap-3">
                        <StatusBadge value={m.role} />
                        {canManage && (
                          <button
                            type="button"
                            onClick={() => removeMember(m)}
                            disabled={busy !== ''}
                            aria-label={`Remove user ${m.user_id}`}
                            className="button-danger button-sm"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Section>

            <div className="grid content-start gap-6">
              {canManage ? (
                <>
                  <Section title="Add a member" padded>
                    <form onSubmit={addMember} className="form-stack">
                      <div className="field-group">
                        <label htmlFor="who" className="field-label">Email or user ID</label>
                        <input
                          id="who" value={member.who} required className="field-control"
                          onChange={(event) => setMember((prev) => ({ ...prev, who: event.target.value }))}
                          placeholder={isAdmin ? 'doctor@example.com' : '42'}
                        />
                        {!isAdmin && (
                          <p className="m-0 text-xs text-slate-500">
                            Email lookup is for platform administrators. Enter the person&apos;s user ID.
                          </p>
                        )}
                      </div>
                      <div className="field-group">
                        <label htmlFor="role" className="field-label">Role in this clinic</label>
                        <select
                          id="role" value={member.role} className="field-control"
                          onChange={(event) => setMember((prev) => ({ ...prev, role: event.target.value }))}
                        >
                          {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                        </select>
                      </div>
                      <button type="submit" disabled={busy !== ''} className="button-primary">
                        {busy === 'add' ? 'Adding...' : 'Add member'}
                      </button>
                    </form>
                  </Section>

                  <Section title="Clinic details" padded>
                    <form onSubmit={saveDetails} className="form-stack">
                      <div className="field-group">
                        <label htmlFor="d-name" className="field-label">Name</label>
                        <input id="d-name" name="name" value={details.name} onChange={setField} required minLength={2} maxLength={100} className="field-control" />
                      </div>
                      <div className="field-group">
                        <label htmlFor="d-address" className="field-label">Address</label>
                        <input id="d-address" name="address" value={details.address} onChange={setField} maxLength={255} className="field-control" />
                      </div>
                      <div className="field-group">
                        <label htmlFor="d-phone" className="field-label">Phone</label>
                        <input id="d-phone" name="phone" type="tel" value={details.phone} onChange={setField} pattern="[+]?[0-9]{10,15}" title="10 to 15 digits" className="field-control" />
                      </div>
                      <button type="submit" disabled={busy !== ''} className="button-secondary">
                        {busy === 'details' ? 'Saving...' : 'Save details'}
                      </button>
                    </form>
                  </Section>
                </>
              ) : (
                <Section title="Clinic details" padded>
                  <div className="grid gap-3 text-sm">
                    <p className="m-0"><span className="text-slate-500">Address: </span>{clinic.address ?? '–'}</p>
                    <p className="m-0"><span className="text-slate-500">Phone: </span>{clinic.phone ?? '–'}</p>
                    <p className="m-0 text-slate-500">Only clinic administrators can edit details or manage members.</p>
                  </div>
                </Section>
              )}
            </div>
          </div>
        </>
      )}
    </main>
  )
}

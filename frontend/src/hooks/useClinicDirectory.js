import { useEffect, useState } from 'react'
import { apiFetch, errorMessage, networkMessage } from '../api/client'

/** The doctors and patients of one clinic, for pickers and name lookups. */
export function useClinicDirectory(clinicId) {
  const [state, setState] = useState({ clinicId: null, doctors: [], patients: [], error: '' })

  useEffect(() => {
    if (!clinicId) return
    let cancelled = false

    async function load() {
      try {
        const [doctorsRes, patientsRes] = await Promise.all([
          apiFetch(`/doctors?clinic_id=${clinicId}`),
          apiFetch(`/patients?clinic_id=${clinicId}`),
        ])
        if (!doctorsRes.ok) throw new Error(await errorMessage(doctorsRes, 'Failed to load doctors.'))
        if (!patientsRes.ok) throw new Error(await errorMessage(patientsRes, 'Failed to load patients.'))

        const [doctors, patients] = await Promise.all([doctorsRes.json(), patientsRes.json()])
        if (!cancelled) setState({ clinicId, doctors, patients, error: '' })
      } catch (err) {
        if (!cancelled) {
          setState({ clinicId, doctors: [], patients: [], error: networkMessage(err) })
        }
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [clinicId])

  // Results for a previous clinic are ignored, so a clinic switch never shows stale data.
  const ready = state.clinicId === clinicId
  return {
    doctors: ready ? state.doctors : [],
    patients: ready ? state.patients : [],
    error: ready ? state.error : '',
    loading: Boolean(clinicId) && !ready,
  }
}

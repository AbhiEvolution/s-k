import { useCallback, useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { apiFetch } from '../api/client'
import { setClinic } from '../features/auth/authSlice'
import { readClaims } from '../lib/claims'
import { AppContext } from './AppContext'

/** Loads the signed-in user's clinics (and doctor profile) once, for every screen. */
export default function AppProvider({ children }) {
  const dispatch = useDispatch()
  const token = useSelector((state) => state.auth.accessToken)
  const clinicId = useSelector((state) => state.auth.clinicId)

  const claims = useMemo(() => readClaims(token), [token])
  const role = claims.role

  const [state, setState] = useState({ ready: false, clinics: [], doctor: null, error: '' })
  const [version, setVersion] = useState(0)
  const reload = useCallback(() => setVersion((v) => v + 1), [])

  useEffect(() => {
    if (!token) return
    let cancelled = false

    async function load() {
      try {
        const [clinicsRes, doctorRes] = await Promise.all([
          apiFetch('/clinics'),
          role === 'doctor' ? apiFetch('/doctors/me') : Promise.resolve(null),
        ])
        if (clinicsRes.status === 401) return // the session ended; the route guard redirects

        const clinics = clinicsRes.ok ? await clinicsRes.json() : []
        // A missing profile (404) is normal for a brand-new doctor.
        const doctor = doctorRes?.ok ? await doctorRes.json() : null
        if (cancelled) return

        setState({
          ready: true,
          clinics,
          doctor,
          error: clinicsRes.ok ? '' : 'Could not load your clinics.',
        })
      } catch {
        if (!cancelled) {
          setState((prev) => ({ ...prev, ready: true, error: 'Unable to connect to the server.' }))
        }
      }
    }

    load()
    return () => {
      cancelled = true
    }
    // `token` changes on every silent refresh; only reload when identity or the version changes.
  }, [claims.userId, role, version, token])

  // Keep the remembered clinic valid: only one I still belong to, else the first.
  useEffect(() => {
    if (!state.ready) return
    if (!state.clinics.some((clinic) => clinic.id === clinicId)) {
      dispatch(setClinic(state.clinics[0]?.id ?? null))
    }
  }, [state.ready, state.clinics, clinicId, dispatch])

  const value = useMemo(() => {
    const activeClinic = state.clinics.find((clinic) => clinic.id === clinicId) ?? null
    return {
      ...state,
      role,
      userId: claims.userId,
      isAdmin: role === 'admin',
      clinicId: activeClinic ? activeClinic.id : null,
      activeClinic,
      selectClinic: (id) => dispatch(setClinic(id)),
      reload,
    }
  }, [state, role, claims.userId, clinicId, dispatch, reload])

  if (!state.ready) {
    return (
      <div className="grid min-h-[60vh] place-items-center" role="status" aria-label="Loading">
        <div className="spinner" />
      </div>
    )
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

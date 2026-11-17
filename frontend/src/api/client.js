import { store } from '../store/store'
import { clearCredentials, setCredentials } from '../features/auth/authSlice'

// Every service is reached through the nginx gateway on the same origin
// (in dev, Vite proxies /api to it), so there is no CORS and no per-service URL.
export const API = '/api/v1'

// If several requests get a 401 at once they must share ONE refresh call.
// Refresh tokens are single-use: a second parallel refresh would look like
// token theft to the server and end the session.
let refreshing = null

function refreshTokens() {
  const { refreshToken } = store.getState().auth
  if (!refreshToken) return Promise.resolve(false)

  if (!refreshing) {
    refreshing = fetch(`${API}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (response) => {
        if (!response.ok) return false
        store.dispatch(setCredentials(await response.json()))
        return true
      })
      .catch(() => false)
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

/**
 * fetch() for authenticated API calls. `path` starts after /api/v1,
 * e.g. apiFetch('/patients?clinic_id=1').
 * On 401 it refreshes the session once and retries; if that fails the user
 * is logged out (the route guard then sends them to /login).
 */
export async function apiFetch(path, options = {}) {
  const send = (token) =>
    fetch(`${API}${path}`, {
      ...options,
      headers: { ...options.headers, Authorization: `Bearer ${token}` },
    })

  const usedToken = store.getState().auth.accessToken
  let response = await send(usedToken)

  if (response.status === 401) {
    const current = store.getState().auth.accessToken
    // Another request may already have refreshed while ours was in flight.
    const renewed = current && current !== usedToken ? true : await refreshTokens()
    if (renewed) response = await send(store.getState().auth.accessToken)
  }

  if (response.status === 401) store.dispatch(clearCredentials())
  return response
}

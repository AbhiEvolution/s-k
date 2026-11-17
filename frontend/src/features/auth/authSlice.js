import { createSlice } from '@reduxjs/toolkit'

// sessionStorage is readable by any script on the page, so an XSS bug could
// steal these. An HttpOnly cookie set by the server would be safer.
const read = (key) => {
  try {
    return sessionStorage.getItem(key)
  } catch {
    return null
  }
}
const write = (key, value) => {
  try {
    if (value === null || value === undefined) sessionStorage.removeItem(key)
    else sessionStorage.setItem(key, String(value))
  } catch {
    // storage unavailable: the session just won't survive a reload
  }
}

const storedClinic = read('clinic_id')

const initialState = {
  accessToken: read('access_token'),
  refreshToken: read('refresh_token'),
  clinicId: storedClinic ? Number(storedClinic) : null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,

  reducers: {
    // payload is the auth service's token response.
    setCredentials: (state, action) => {
      state.accessToken = action.payload.access_token
      state.refreshToken = action.payload.refresh_token
      write('access_token', state.accessToken)
      write('refresh_token', state.refreshToken)
    },

    setClinic: (state, action) => {
      state.clinicId = action.payload
      write('clinic_id', action.payload)
    },

    clearCredentials: (state) => {
      state.accessToken = null
      state.refreshToken = null
      state.clinicId = null
      write('access_token', null)
      write('refresh_token', null)
      write('clinic_id', null)
    },
  },
})

export const { setCredentials, setClinic, clearCredentials } = authSlice.actions

export default authSlice.reducer

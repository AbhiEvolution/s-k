
import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  accessToken: sessionStorage.getItem('access_token'),
}

const authSlice = createSlice({
  name: 'auth',
  initialState,

  reducers: {
    setCredentials: (state, action) => {
      state.accessToken = action.payload.access_token

      sessionStorage.setItem(
        'access_token',
        action.payload.access_token
      )
    },

    clearCredentials: (state) => {
      state.accessToken = null
      sessionStorage.removeItem('access_token')
    },
  },
})

export const { setCredentials, clearCredentials } = authSlice.actions

export default authSlice.reducer

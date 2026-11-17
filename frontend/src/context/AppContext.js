import { createContext, useContext } from 'react'

export const AppContext = createContext(null)

/** Everything the signed-in screens share: who I am, my clinics, the active clinic. */
export function useApp() {
  const value = useContext(AppContext)
  if (!value) throw new Error('useApp must be used inside <AppProvider>')
  return value
}

/**
 * Read the claims out of a JWT, for DISPLAY decisions only (which menu items to
 * show). This does NOT verify anything and must never be trusted: every service
 * re-checks the token on every request, so editing it in dev tools gains nothing.
 */
export function readClaims(token) {
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const json = decodeURIComponent(
      atob(payload.padEnd(Math.ceil(payload.length / 4) * 4, '='))
        .split('')
        .map((char) => `%${char.charCodeAt(0).toString(16).padStart(2, '0')}`)
        .join('')
    )
    const claims = JSON.parse(json)
    return { userId: Number(claims.sub), role: String(claims.role ?? '') }
  } catch {
    return { userId: null, role: '' }
  }
}

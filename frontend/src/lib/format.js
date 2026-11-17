// The API speaks UTC, so the screens show UTC (and say so).
const WHEN = {
  timeZone: 'UTC',
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
}

export const formatWhen = (iso) =>
  `${new Date(iso).toLocaleString('en-GB', WHEN)} UTC`

export const formatTime = (iso) =>
  new Date(iso).toLocaleTimeString('en-GB', { timeZone: 'UTC', hour: '2-digit', minute: '2-digit' })

export const formatDay = (iso) =>
  new Date(iso).toLocaleDateString('en-GB', {
    timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long',
  })

export const utcDate = (value = new Date()) => new Date(value).toISOString().slice(0, 10)

export const humanize = (value) => (value ? value.replaceAll('_', ' ') : '')

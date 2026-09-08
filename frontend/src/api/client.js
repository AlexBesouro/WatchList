// The only file that talks to the network. Everything else calls these
// functions, so a change of host or of error handling happens in one place.

// Vite inlines import.meta.env at build time; the fallback is the port uvicorn
// serves on, which is what a fresh clone needs to work with no .env at all.
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Carries the HTTP status as well as the message, so a caller can tell "wrong
// password" (401) from "the server is down" (0) without parsing text.
export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// FastAPI answers a validation failure with a list of objects and everything
// else with a plain string, so both shapes are folded into one sentence here.
function readDetail(body, status) {
  const detail = body?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(', ')
  return `The server answered ${status}.`
}

async function request(path, { method = 'GET', body, token } = {}) {
  let response
  try {
    response = await fetch(BASE_URL + path, {
      method,
      headers: {
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    // fetch only rejects when the request never reached a server: no network,
    // API stopped, CORS refused. There is no status to report, hence 0.
    throw new ApiError(0, 'The server did not answer. Is the API running?')
  }

  // 204 has no body at all, and response.json() on an empty body throws.
  if (response.status === 204) return null

  // let and not const: the value is assigned inside the try and read after it.
  let payload = null
  try {
    payload = await response.json()
  } catch {
    // A body that is empty or not JSON at all; the status still says enough.
  }

  if (!response.ok) throw new ApiError(response.status, readDetail(payload, response.status))
  return payload
}

// The public list. An empty term means "popular", which is what the home page
// wants, so the parameter is simply left out rather than sent empty.
export function fetchMovies({ query = '', page = 1 } = {}) {
  const params = new URLSearchParams({ page })
  if (query) params.set('query', query)
  return request(`/movies?${params}`)
}

export function signUp(form) {
  return request('/users', { method: 'POST', body: form })
}

export function signIn(credentials) {
  return request('/login', { method: 'POST', body: credentials })
}

export function fetchMe(token) {
  return request('/users/me', { token })
}

// `list` is 'favorites' or 'watch-later' — the same two names the back-end uses
// as route prefixes, so one set of functions serves both lists. No path here ends
// in a slash: the API declares every route without one.
export function fetchSaved(token, list) {
  return request(`/${list}`, { token })
}

export function addSaved(token, list, movie) {
  return request(`/${list}`, { method: 'POST', token, body: movie })
}

export function removeSaved(token, list, tmdbId) {
  return request(`/${list}/${tmdbId}`, { method: 'DELETE', token })
}

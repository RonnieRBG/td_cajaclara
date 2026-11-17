const ACCESS_TOKEN_KEY = 'cc_access'
const REFRESH_TOKEN_KEY = 'cc_refresh'
const SESSION_EXPIRED_EVENT = 'auth:session-expired'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '')

let refreshPromise = null
let expirationEventDispatched = false

export class ApiError extends Error {
  constructor(message, { code = 'API_ERROR', status = null, validationErrors = {} } = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.validationErrors = validationErrors
  }
}

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },
  get hasTokens() {
    return Boolean(this.access || this.refresh)
  },
  save({ access, refresh }) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
    expirationEventDispatched = false
  },
  clear() {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

function apiUrl(path) {
  if (!API_BASE_URL) {
    throw new ApiError('Falta configurar VITE_API_BASE_URL.', { code: 'CONFIGURATION_ERROR' })
  }

  return `${API_BASE_URL}/${path.replace(/^\/+/, '')}`
}

function redactTokenLikeValues(value) {
  return value.replace(
    /[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,
    '[token omitido]'
  )
}

function validationMessages(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return {}

  return Object.fromEntries(
    Object.entries(payload)
      .filter(([field]) => !['detail', 'error', 'access', 'refresh', 'token', 'password'].includes(field))
      .map(([field, messages]) => [
        field,
        redactTokenLikeValues(
          (Array.isArray(messages) ? messages : [messages])
            .filter((message) => typeof message === 'string')
            .join(' ')
        )
      ])
      .filter(([, message]) => message)
  )
}

function createResponseError(status, payload) {
  const validationErrors = validationMessages(payload)
  const detail = typeof payload?.detail === 'string' ? payload.detail : ''
  const error = typeof payload?.error === 'string' ? payload.error : ''
  const message = detail || error || Object.values(validationErrors)[0] || `Error HTTP ${status}.`

  return new ApiError(redactTokenLikeValues(message), {
    code: status === 401 ? 'UNAUTHORIZED' : status === 429 ? 'RATE_LIMITED' : 'API_ERROR',
    status,
    validationErrors
  })
}

async function readResponse(response) {
  if (response.status === 204 || response.status === 205) return null

  const text = await response.text()
  if (!text.trim()) return null

  const contentType = response.headers.get('content-type') || ''
  if (!contentType.toLowerCase().includes('application/json')) return null

  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

function requestOptions({ method = 'GET', body, headers = {}, accessToken } = {}) {
  const requestHeaders = new Headers(headers)
  requestHeaders.set('Accept', 'application/json')

  const options = { method, headers: requestHeaders }
  if (body !== undefined) {
    requestHeaders.set('Content-Type', 'application/json')
    options.body = JSON.stringify(body)
  }
  if (accessToken) requestHeaders.set('Authorization', `Bearer ${accessToken}`)

  return options
}

function dispatchSessionExpired() {
  if (expirationEventDispatched) return

  expirationEventDispatched = true
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
}

async function renewTokens() {
  if (!tokenStore.refresh) return false

  if (!refreshPromise) {
    refreshPromise = (async () => {
      const url = apiUrl('/auth/refresh/')
      let response
      let payload

      try {
        response = await fetch(
          url,
          requestOptions({ method: 'POST', body: { refresh: tokenStore.refresh } })
        )
        payload = await readResponse(response)
      } catch (error) {
        if (error instanceof TypeError) return false
        throw error
      }

      if (!response.ok || !payload?.access || !payload?.refresh) return false

      tokenStore.save({ access: payload.access, refresh: payload.refresh })
      return true
    })().finally(() => {
      refreshPromise = null
    })
  }

  return refreshPromise
}

async function send(path, options, { authenticated, retryAfterRefresh }) {
  const accessToken = authenticated ? tokenStore.access : null
  let response

  try {
    response = await fetch(apiUrl(path), requestOptions({ ...options, accessToken }))
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiError('No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.', {
        code: 'NETWORK_ERROR'
      })
    }
    throw error
  }

  const payload = await readResponse(response)

  if (response.status === 401 && authenticated && retryAfterRefresh) {
    if (await renewTokens()) {
      return send(path, options, { authenticated, retryAfterRefresh: false })
    }

    tokenStore.clear()
    dispatchSessionExpired()
    throw new ApiError('Tu sesión expiró. Inicia sesión nuevamente.', {
      code: 'SESSION_EXPIRED',
      status: 401
    })
  }

  if (!response.ok) throw createResponseError(response.status, payload)
  return payload
}

export function apiRequest(path, options = {}) {
  const { authenticated = false, retryAfterRefresh = false, ...request } = options
  return send(path, request, { authenticated, retryAfterRefresh })
}

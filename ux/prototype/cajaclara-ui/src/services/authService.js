import { apiRequest, ApiError, tokenStore } from './apiClient'
import { DEMO_ACCESS_ENABLED } from './optionsService'

// TODO: eliminar acceso demo temporal.
const DEMO_SESSION_KEY = 'cc_demo_session'
const DEMO_CREDENTIALS_DIGEST = '45294bc70db3edb97138ec9f32d0a7a31384fc62243b8f1c91534aaca984771a'

function hasDemoSession() {
  return DEMO_ACCESS_ENABLED && window.sessionStorage.getItem(DEMO_SESSION_KEY) === 'true'
}

async function matchesDemoCredentials({ username, password }) {
  const credentials = new TextEncoder().encode(`${username}\0${password}`)
  const digest = await window.crypto.subtle.digest('SHA-256', credentials)
  const digestHex = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('')
  return digestHex === DEMO_CREDENTIALS_DIGEST
}

function requireTokenPair(payload) {
  if (typeof payload?.access !== 'string' || typeof payload?.refresh !== 'string') {
    throw new ApiError('El servidor devolvió una respuesta de autenticación incompleta.', {
      code: 'INVALID_AUTH_RESPONSE'
    })
  }

  return { access: payload.access, refresh: payload.refresh }
}

export async function login(credentials) {
  // TODO: eliminar acceso demo temporal.
  if (DEMO_ACCESS_ENABLED) {
    window.sessionStorage.removeItem(DEMO_SESSION_KEY)
    tokenStore.clear()

    if (!await matchesDemoCredentials(credentials)) {
      throw new ApiError('Usuario o contraseña incorrectos.', {
        code: 'INVALID_CREDENTIALS',
        status: 401
      })
    }

    window.sessionStorage.setItem(DEMO_SESSION_KEY, 'true')
    return { nombre: 'Demo CajaClara', isDemo: true }
  }

  const payload = await apiRequest('/auth/login/', {
    method: 'POST',
    body: {
      username: credentials.username,
      password: credentials.password
    }
  })

  if (!payload?.usuario || typeof payload.usuario !== 'object') {
    throw new ApiError('El servidor devolvió una respuesta de autenticación incompleta.', {
      code: 'INVALID_AUTH_RESPONSE'
    })
  }

  tokenStore.save(requireTokenPair(payload))
  return payload.usuario
}

export async function refreshToken() {
  if (DEMO_ACCESS_ENABLED) {
    throw new ApiError('La sesión de demostración no utiliza tokens.', { code: 'SESSION_EXPIRED' })
  }

  const refresh = tokenStore.refresh
  if (!refresh) {
    throw new ApiError('No hay una sesión que se pueda renovar.', { code: 'SESSION_EXPIRED' })
  }

  try {
    const payload = await apiRequest('/auth/refresh/', {
      method: 'POST',
      body: { refresh }
    })
    tokenStore.save(requireTokenPair(payload))
    return payload.access
  } catch (error) {
    tokenStore.clear()
    window.dispatchEvent(new Event('auth:session-expired'))
    if (error instanceof ApiError && error.status === 401) {
      throw new ApiError('Tu sesión expiró. Inicia sesión nuevamente.', {
        code: 'SESSION_EXPIRED',
        status: 401
      })
    }
    throw error
  }
}

export async function logout() {
  // TODO: eliminar acceso demo temporal.
  if (DEMO_ACCESS_ENABLED) {
    window.sessionStorage.removeItem(DEMO_SESSION_KEY)
    tokenStore.clear()
    return
  }

  const refresh = tokenStore.refresh
  if (!refresh) {
    tokenStore.clear()
    window.sessionStorage.removeItem(DEMO_SESSION_KEY)
    return
  }

  try {
    await apiRequest('/auth/logout/', {
      method: 'POST',
      body: { refresh }
    })
  } finally {
    tokenStore.clear()
    window.sessionStorage.removeItem(DEMO_SESSION_KEY)
  }
}

export function getProfile() {
  // TODO: eliminar acceso demo temporal.
  if (hasDemoSession()) {
    return Promise.resolve({ nombre: 'Demo CajaClara', isDemo: true })
  }

  if (DEMO_ACCESS_ENABLED) {
    return Promise.reject(new ApiError('No hay una sesión de demostración activa.', {
      code: 'SESSION_EXPIRED'
    }))
  }

  return apiRequest('/auth/perfil/', {
    authenticated: true,
    retryAfterRefresh: true
  })
}

export function isAuthenticated() {
  // TODO: eliminar acceso demo temporal.
  if (DEMO_ACCESS_ENABLED) return hasDemoSession()
  return tokenStore.hasTokens
}

export function clearSession() {
  tokenStore.clear()
  window.sessionStorage.removeItem(DEMO_SESSION_KEY)
}

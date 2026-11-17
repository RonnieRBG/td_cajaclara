import { apiRequest, ApiError, tokenStore } from './apiClient'

function requireTokenPair(payload) {
  if (typeof payload?.access !== 'string' || typeof payload?.refresh !== 'string') {
    throw new ApiError('El servidor devolvió una respuesta de autenticación incompleta.', {
      code: 'INVALID_AUTH_RESPONSE'
    })
  }

  return { access: payload.access, refresh: payload.refresh }
}

export async function login(credentials) {
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
  const refresh = tokenStore.refresh
  if (!refresh) {
    tokenStore.clear()
    return
  }

  try {
    await apiRequest('/auth/logout/', {
      method: 'POST',
      body: { refresh }
    })
  } finally {
    tokenStore.clear()
  }
}

export function getProfile() {
  return apiRequest('/auth/perfil/', {
    authenticated: true,
    retryAfterRefresh: true
  })
}

export function isAuthenticated() {
  return tokenStore.hasTokens
}

export function clearSession() {
  tokenStore.clear()
}

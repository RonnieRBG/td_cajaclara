import { ref } from 'vue'
import * as authService from '@/services/authService'
import { ApiError } from '@/services/apiClient'

const user = ref(null)
const isAuthenticated = ref(false)
const isLoading = ref(false)
const error = ref(null)
let restorationPromise = null

function authErrorFrom(error) {
  if (error instanceof ApiError && error.code === 'SESSION_EXPIRED') {
    return {
      code: 'SESSION_EXPIRED',
      message: 'Tu sesión expiró. Inicia sesión nuevamente.'
    }
  }
  if (error instanceof ApiError && error.status === 401) {
    return {
      code: 'INVALID_CREDENTIALS',
      message: 'Usuario o contraseña incorrectos.'
    }
  }
  if (error instanceof ApiError && error.status === 429) {
    return {
      code: 'RATE_LIMITED',
      message: 'Hubo demasiados intentos. Espera un minuto e inténtalo de nuevo.'
    }
  }
  if (error instanceof ApiError && error.code === 'NETWORK_ERROR') {
    return {
      code: 'CONNECTION_ERROR',
      message: 'No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.'
    }
  }

  return {
    code: 'AUTHENTICATION_ERROR',
    message: error instanceof Error ? error.message : 'No se pudo completar la autenticación.'
  }
}

async function login(credentials) {
  isLoading.value = true
  error.value = null

  try {
    user.value = await authService.login(credentials)
    isAuthenticated.value = true
    return true
  } catch (cause) {
    user.value = null
    isAuthenticated.value = false
    error.value = authErrorFrom(cause)
    return false
  } finally {
    isLoading.value = false
  }
}

async function restoreSession() {
  if (isAuthenticated.value && user.value) return true
  if (!authService.isAuthenticated()) return false
  if (restorationPromise) return restorationPromise

  restorationPromise = (async () => {
    isLoading.value = true
    error.value = null

    try {
      user.value = await authService.getProfile()
      isAuthenticated.value = true
      return true
    } catch (cause) {
      user.value = null
      isAuthenticated.value = false
      error.value = authErrorFrom(cause)
      return false
    } finally {
      isLoading.value = false
      restorationPromise = null
    }
  })()

  return restorationPromise
}

async function renewToken() {
  try {
    await authService.refreshToken()
    return true
  } catch (cause) {
    error.value = authErrorFrom(cause)
    user.value = null
    isAuthenticated.value = false
    return false
  }
}

async function logout() {
  isLoading.value = true
  error.value = null

  try {
    await authService.logout()
    return true
  } catch (cause) {
    error.value = authErrorFrom(cause)
    return false
  } finally {
    user.value = null
    isAuthenticated.value = false
    isLoading.value = false
  }
}

function expireSession() {
  authService.clearSession()
  user.value = null
  isAuthenticated.value = false
  error.value = {
    code: 'SESSION_EXPIRED',
    message: 'Tu sesión expiró. Inicia sesión nuevamente.'
  }
}

function clearError() {
  error.value = null
}

export function useAuth() {
  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    restoreSession,
    logout,
    renewToken,
    expireSession,
    clearError
  }
}

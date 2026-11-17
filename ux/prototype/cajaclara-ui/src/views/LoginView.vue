<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const router = useRouter()
const { login, isLoading, error, clearError } = useAuth()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const attemptedSubmit = ref(false)
const usernameInput = ref(null)
const passwordInput = ref(null)

const usernameError = computed(() => (
  attemptedSubmit.value && !username.value.trim() ? 'Ingresa tu usuario.' : ''
))
const passwordError = computed(() => (
  attemptedSubmit.value && !password.value ? 'Ingresa tu contraseña.' : ''
))
const credentialsInvalid = computed(() => error.value?.code === 'INVALID_CREDENTIALS')
const errorMessage = computed(() => {
  if (
    route.query.reason === 'logout-error'
    && !['INVALID_CREDENTIALS', 'RATE_LIMITED'].includes(error.value?.code)
  ) {
    return 'La sesión se cerró en este dispositivo, pero no se pudo confirmar el cierre con el servidor.'
  }
  if (error.value?.message) return error.value.message
  if (route.query.reason === 'expired') return 'Tu sesión expiró. Inicia sesión nuevamente para continuar.'
  if (route.query.reason === 'connection') {
    return 'No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.'
  }
  return ''
})

onMounted(async () => {
  await nextTick()
  usernameInput.value?.focus()
})

async function submitLogin() {
  attemptedSubmit.value = true
  clearError()

  if (usernameError.value) {
    usernameInput.value?.focus()
    return
  }
  if (passwordError.value) {
    passwordInput.value?.focus()
    return
  }

  const loggedIn = await login({
    username: username.value.trim(),
    password: password.value
  })

  if (!loggedIn) {
    if (credentialsInvalid.value) usernameInput.value?.focus()
    return
  }

  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
  const safeRedirect = redirect.startsWith('/') && !redirect.startsWith('//') && redirect !== '/login'
    ? redirect
    : { name: 'Dashboard' }

  await router.replace(safeRedirect)
}
</script>

<template>
  <main id="main-content" class="login-screen">
    <section class="login-card" aria-labelledby="login-title">
      <div class="login-brand" aria-label="CajaClara">
        <span class="login-brand__mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="4" width="20" height="16" rx="3" />
            <path d="M7 15h0M12 15h0M17 15h0M7 11h10" />
          </svg>
        </span>
        <span>CajaClara</span>
      </div>

      <p class="login-kicker">Caja digital para tu negocio</p>
      <h1 id="login-title">Inicia sesión</h1>
      <p class="login-description">
        Organiza tu caja, tus ventas y tus cobros desde un solo lugar.
      </p>

      <form class="login-form" novalidate @submit.prevent="submitLogin">
        <div class="login-field">
          <label for="username">Usuario</label>
          <input
            id="username"
            ref="usernameInput"
            v-model="username"
            name="username"
            type="text"
            autocomplete="username"
            :aria-describedby="usernameError ? 'username-error' : credentialsInvalid ? 'auth-error' : undefined"
            :aria-invalid="Boolean(usernameError || credentialsInvalid)"
            :aria-required="true"
            @input="clearError"
          />
          <p v-if="usernameError" id="username-error" class="field-error" aria-live="polite">
            {{ usernameError }}
          </p>
        </div>

        <div class="login-field">
          <label for="password">Contraseña</label>
          <div class="password-control">
            <input
              id="password"
              ref="passwordInput"
              v-model="password"
              name="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              :aria-describedby="passwordError ? 'password-error' : credentialsInvalid ? 'auth-error' : undefined"
              :aria-invalid="Boolean(passwordError || credentialsInvalid)"
              :aria-required="true"
              @input="clearError"
            />
            <button
              type="button"
              class="password-toggle"
              :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              :aria-pressed="showPassword"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? 'Ocultar' : 'Mostrar' }}
            </button>
          </div>
          <p v-if="passwordError" id="password-error" class="field-error" aria-live="polite">
            {{ passwordError }}
          </p>
        </div>

        <p
          v-if="errorMessage"
          id="auth-error"
          class="login-message"
          :class="{ 'login-message--invalid': credentialsInvalid }"
          role="alert"
          aria-live="assertive"
        >
          {{ errorMessage }}
        </p>

        <button class="login-submit" type="submit" :disabled="isLoading">
          <span v-if="isLoading" class="login-spinner" aria-hidden="true"></span>
          {{ isLoading ? 'Iniciando sesión…' : 'Iniciar sesión' }}
        </button>
      </form>

      <p class="login-access-note">
        El acceso lo administra CajaClara. No existe registro público; solicita una cuenta a un administrador.
      </p>
    </section>
  </main>
</template>

<style scoped>
.login-screen {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: clamp(var(--space-4), 5vw, var(--space-12));
  background:
    radial-gradient(ellipse at 18% 12%, rgba(15, 118, 110, 0.1), transparent 38%),
    var(--color-bg-app);
}

.login-card {
  width: min(100%, 456px);
  padding: clamp(var(--space-6), 6vw, var(--space-10));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-bg-surface);
  box-shadow: var(--shadow-lg);
}

.login-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-main);
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 800;
}

.login-brand__mark {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border-radius: var(--radius-md);
  background: var(--color-brand-primary);
  color: var(--color-text-on-dark);
}

.login-kicker {
  margin-top: var(--space-8);
  color: var(--color-brand-primary);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-card h1 {
  margin-top: var(--space-2);
  color: var(--color-text-main);
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 5vw, 2rem);
  letter-spacing: -0.04em;
  line-height: 1.2;
}

.login-description {
  margin-top: var(--space-2);
  color: var(--color-text-secondary);
  font-size: 0.95rem;
}

.login-form {
  display: grid;
  gap: var(--space-5);
  margin-top: var(--space-8);
}

.login-field {
  display: grid;
  gap: var(--space-2);
}

.login-field label {
  color: var(--color-text-main);
  font-size: 0.875rem;
  font-weight: 700;
}

.login-field input {
  width: 100%;
  min-height: 48px;
  padding: 0 var(--space-4);
  border: 1px solid #94a3b8;
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--color-text-main);
  font: inherit;
}

.login-field input[aria-invalid='true'] {
  border-color: var(--color-danger);
}

.login-field input:focus-visible,
.password-toggle:focus-visible,
.login-submit:focus-visible {
  outline: 3px solid var(--color-brand-primary);
  outline-offset: 3px;
}

.password-control {
  position: relative;
}

.password-control input {
  padding-right: 88px;
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: var(--space-2);
  min-height: 36px;
  padding: 0 var(--space-2);
  transform: translateY(-50%);
  border-radius: var(--radius-xs);
  color: var(--color-brand-primary);
  font-size: 0.78rem;
  font-weight: 800;
}

.password-toggle:hover {
  background: var(--color-brand-primary-light);
}

.field-error {
  color: #b91c1c;
  font-size: 0.8rem;
  font-weight: 600;
}

.login-message {
  padding: var(--space-3) var(--space-4);
  border: 1px solid #fca5a5;
  border-radius: var(--radius-sm);
  background: #fef2f2;
  color: #991b1b;
  font-size: 0.875rem;
  font-weight: 600;
}

.login-submit {
  display: inline-flex;
  min-height: 50px;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: 1px solid var(--color-brand-primary);
  border-radius: var(--radius-sm);
  background: var(--color-brand-primary);
  color: var(--color-text-on-dark);
  font: inherit;
  font-weight: 800;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}

.login-submit:hover:not(:disabled) {
  border-color: var(--color-brand-primary-hover);
  background: var(--color-brand-primary-hover);
}

.login-submit:disabled {
  cursor: wait;
  opacity: 0.72;
}

.login-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #fff;
  border-radius: 50%;
  animation: login-spin 0.7s linear infinite;
}

.login-access-note {
  margin-top: var(--space-6);
  padding-top: var(--space-5);
  border-top: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  line-height: 1.6;
}

@keyframes login-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 420px) {
  .login-screen {
    padding: var(--space-3);
  }

  .login-card {
    padding: var(--space-6) var(--space-5);
    border-radius: var(--radius-lg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-spinner {
    animation-duration: 1.5s;
  }
}
</style>

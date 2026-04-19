<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

const router = useRouter()
const { login } = useAuth()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
    error.value = ''
    loading.value = true
    try {
        await login({ email: email.value, password: password.value })
        router.push('/')
    } catch (err) {
        if (err.response?.status === 401) {
            error.value = 'Email o contraseña incorrectos.'
        } else {
            error.value = 'Error al iniciar sesión. Por favor, inténtalo de nuevo.'
        }
    } finally {
        loading.value = false
    }
}
</script>

<template>
  <div class="auth-container">
    <h1>Iniciar sesión</h1>
    <form @submit.prevent="handleSubmit">
        <label>
            Email
            <input
                v-model="email"
                type="email"
                required
                autocomplete="email"
                :disabled="loading"
            />
        </label>
        <label>
        Contraseña
        <input
          v-model="password"
          type="password"
          required
          minlength="8"
          autocomplete="current-password"
          :disabled="loading"
        />
      </label>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Ingresando...' : 'Ingresar' }}
      </button>

      <p v-if="error" class="error">{{ error }}</p>
    </form>

    <p class="link">
      ¿No tenés cuenta?
      <router-link to="/register">Registrate</router-link>
    </p>
  </div>
</template>

<style scoped>
.auth-container {
  max-width: 400px;
  margin: 2rem auto;
  padding: 1.5rem;
}
form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
input {
  padding: 0.5rem;
  font-size: 1rem;
}
button {
  padding: 0.75rem;
  font-size: 1rem;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.error {
  color: #c00;
  margin: 0;
}
.link {
  margin-top: 1rem;
  text-align: center;
}
</style>
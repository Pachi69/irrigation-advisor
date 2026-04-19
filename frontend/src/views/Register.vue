<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

const router = useRouter()
const { register, login } = useAuth()

const name = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''

  if (password.value !== passwordConfirm.value) {
    error.value = 'Las contraseñas no coinciden'
    return
  }

  loading.value = true
  try {
    await register({
      name: name.value,
      email: email.value,
      password: password.value,
    })
    // Auto-login tras registro exitoso
    await login({ email: email.value, password: password.value })
    router.push('/')
  } catch (err) {
    if (err.response?.status === 409) {
      error.value = 'Ya existe una cuenta con ese email'
    } else if (err.response?.status === 422) {
      error.value = 'Datos inválidos. Revisá el formulario.'
    } else {
      error.value = 'Error al registrar. Intentá de nuevo.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <h1>Crear cuenta</h1>
    <form @submit.prevent="handleSubmit">
      <label>
        Nombre
        <input
          v-model="name"
          type="text"
          required
          minlength="2"
          maxlength="100"
          autocomplete="name"
          :disabled="loading"
        />
      </label>

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
          maxlength="128"
          autocomplete="new-password"
          :disabled="loading"
        />
      </label>

      <label>
        Confirmar contraseña
        <input
          v-model="passwordConfirm"
          type="password"
          required
          minlength="8"
          maxlength="128"
          autocomplete="new-password"
          :disabled="loading"
        />
      </label>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Creando cuenta...' : 'Registrarme' }}
      </button>

      <p v-if="error" class="error">{{ error }}</p>
    </form>

    <p class="link">
      ¿Ya tenés cuenta?
      <router-link to="/login">Iniciar sesión</router-link>
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
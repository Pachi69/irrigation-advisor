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
  <div class="min-h-[calc(100svh-3.5rem)] flex items-center justify-center px-4 py-10">
    <div class="w-full max-w-sm">

      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">Crear cuenta</h1>
        <p class="text-gray-500 text-sm mt-1">Sistema de recomendación de riego</p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre</label>
          <input
            v-model="name"
            type="text"
            required
            minlength="2"
            maxlength="100"
            autocomplete="name"
            :disabled="loading"
            placeholder="Juan Pérez"
            class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Email</label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="email"
            :disabled="loading"
            placeholder="productor@ejemplo.com"
            class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Contraseña</label>
          <input
            v-model="password"
            type="password"
            required
            minlength="8"
            maxlength="128"
            autocomplete="new-password"
            :disabled="loading"
            placeholder="Mínimo 8 caracteres"
            class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Confirmar contraseña</label>
          <input
            v-model="passwordConfirm"
            type="password"
            required
            minlength="8"
            maxlength="128"
            autocomplete="new-password"
            :disabled="loading"
            placeholder="••••••••"
            class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
          />
        </div>

        <div
          v-if="error"
          class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl"
        >
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-green-800 hover:bg-green-700 text-white font-bold py-3.5 rounded-xl text-base transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-2"
        >
          {{ loading ? 'Creando cuenta...' : 'Registrarme' }}
        </button>
      </form>

      <p class="text-center text-sm text-gray-500 mt-6">
        ¿Ya tenés cuenta?
        <RouterLink to="/login" class="text-green-700 font-semibold hover:underline">
          Iniciar sesión
        </RouterLink>
      </p>

    </div>
  </div>
</template>

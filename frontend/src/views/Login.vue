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
  <div class="min-h-[calc(100svh-3.5rem)] flex items-center justify-center px-4 py-10">
    <div class="w-full max-w-sm">

      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">Iniciar sesión</h1>
        <p class="text-gray-500 text-sm mt-1">Sistema de recomendación de riego </p>
      </div>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">
            Email
          </label>
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
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">
            Contraseña
          </label>
          <input
            v-model="password"
            type="password"
            required
            minlength="8"
            autocomplete="current-password"
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
          {{ loading ? 'Ingresando...' : 'Ingresar' }}
        </button>
      </form>
      <p class="text-center text-sm text-gray-500 mt-6">
        ¿No tenés cuenta?
        <RouterLink to="/register" class="text-green-700 font-semibold hover:underline">
          Registrate
        </RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { RouterView, RouterLink, useRouter } from 'vue-router'
import { useAuth } from './stores/auth'
import { onMounted } from 'vue'
import { Leaf } from 'lucide-vue-next'

const router = useRouter()
const { isAuthenticated, isAdmin, logout, fetchMe, user } = useAuth()

onMounted(async () => {
  if (isAuthenticated.value && !user.value) {
    try {
      await fetchMe()
    } catch {
      logout()
    }
  }
})

function handleLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-svh flex flex-col">
    <nav class="bg-green-800 sticky top-0 z-40 shadow-md">
      <div class="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <RouterLink to="/" class="flex items-center gap-2 text-white font-bold text-base tracking-tight">
          <Leaf class="w-5 h-5 text-green-300" :stroke-width="2.5" />
          Irrigation Advisor
        </RouterLink>

        <template v-if="isAuthenticated">
          <div class="flex items-center gap-1">
            <RouterLink 
              to="/fields" 
              class="px-3 py-1.5 rounded-lg text-sm font-medium text-green-100 hover:bg-green-700
              hover:text-white transition-colors"
              active-class="bg-green-700 text-white"
            >
              Mis Campos
            </RouterLink>
            <RouterLink
              v-if="isAdmin"
              to="/admin/fields"
              class="px-3 py-1.5 rounded-lg text-sm font-semibold text-yellow-300 hover:bg-green-700
              transition-colors"
              active-class="bg-green-700"
            >
              Admin
            </RouterLink>
            <button
              @click="handleLogout"
              class="ml-1 px-3 py-1.5 rounded-lg text-sm font-medium text-green-100 border border-green-600
              hover:bg-green-700 hover:text-white transition-colors"
            >
              Salir
            </button>
          </div>
        </template>

        <template v-else>
          <div class="flex items-center gap-2">
            <RouterLink 
              to="/login"
              class="px-3 py-1.5 rounded-lg text-sm font-medium text-green-100 hover:bg-green-700 transition-colors"
            >
              Ingresar
            </RouterLink>
            <RouterLink
              to="/register"
              class="px-3 py-1.5 rounded-lg text-sm font-semibold bg-white text-green-800 hover:bg-green-50 transition-colors"
            >
              Registrarse
            </RouterLink>
          </div>
        </template>
      </div>
    </nav>

    <main class="flex-1 bg-gray-50">
      <RouterView />
    </main>
  </div>
</template>

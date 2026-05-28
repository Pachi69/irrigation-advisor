<script setup>
import { useAuth } from '../stores/auth'
import { useRouter } from 'vue-router'
import { LogOut, User } from 'lucide-vue-next'

const { user, logout } = useAuth()
const router = useRouter()

function handleLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <div class="max-w-[640px] mx-auto px-5 md:px-8 pt-6 pb-8">
    <h1 class="text-2xl font-bold text-ink tracking-tight mb-6">Mi cuenta</h1>

    <div class="bg-surface border border-line rounded-2xl p-5 flex items-center gap-4 mb-4">
      <div class="w-12 h-12 rounded-full bg-primary-soft text-primary text-lg font-bold flex items-center justify-center">
        {{ user?.email?.[0]?.toUpperCase() || 'U' }}
      </div>
      <div class="flex-1 min-w-0">
        <div class="font-bold text-ink">{{ user?.name || 'Productor' }}</div>
        <div class="text-sm text-muted truncate">{{ user?.email }}</div>
      </div>
      <User :size="18" class="text-muted" />
    </div>

    <button
      @click="handleLogout"
      class="w-full flex items-center justify-center gap-2 bg-surface border border-line text-ink font-bold px-4 py-3 rounded-xl hover:bg-chip transition-colors"
    >
      <LogOut :size="16" /> Cerrar sesión
    </button>
  </div>
</template>
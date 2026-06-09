<script setup>
/**
 * App.vue — shell con navegación responsiva.
 *
 * Mobile (PWA Android): brand bar slim arriba + bottom tab bar (Inicio · Campos · Cuenta).
 * Desktop (Chrome web): top nav con logo + tabs + perfil.
 *
 * Mantiene la misma estructura de routing que el original.
 */
import { RouterView, RouterLink, useRouter, useRoute } from 'vue-router'
import { useAuth } from './stores/auth'
import { onMounted, computed } from 'vue'
import { subscribeToPush } from './services/push'
import { Home, Sprout, User, Shield, FlaskConical } from 'lucide-vue-next'
import InstallPrompt from './components/InstallPrompt.vue'


const router = useRouter()
const route = useRoute()
const { isAuthenticated, isAdmin, fetchMe, user } = useAuth()

onMounted(async () => {
  if (isAuthenticated.value && !user.value) {
    try { await fetchMe() } catch { logout() }
  }
  if (isAuthenticated.value && 'Notification' in window && Notification.permission === 'granted') {
    subscribeToPush().catch(() => {})
  }
})

// Highlight active tab from route
const activeTab = computed(() => {
  if (route.path.startsWith('/fields')) return 'fields'
  if (route.path.startsWith('/admin'))  return 'admin'
  if (route.path.startsWith('/account')) return 'account'
  if (route.path.startsWith('/demo')) return 'demo'
  return 'home'
})
</script>

<template>
  <div class="min-h-svh flex flex-col bg-paper text-ink font-sans">

    <!-- ─── Desktop nav (md+) ─── -->
    <nav v-if="isAuthenticated" class="hidden md:flex items-center bg-surface border-b border-line px-8 h-[60px] gap-9">
      <RouterLink to="/" class="flex items-center gap-2.5">
        <span class="text-primary">
          <!-- Drop logo (custom svg) -->
          <svg width="26" height="26" viewBox="0 0 32 32" fill="none">
            <path d="M16 3c-4 6-7 9-7 13a7 7 0 0 0 14 0c0-4-3-7-7-13z" fill="currentColor"/>
          </svg>
        </span>
        <span class="text-lg font-bold tracking-tight">
          Irrigation Advisor
        </span>
      </RouterLink>

      <div class="flex gap-1 flex-1">
        <RouterLink to="/" class="nav-tab" :class="{ 'nav-tab-active': activeTab === 'home' }">
          <Home :size="16" /> Inicio
        </RouterLink>
        <RouterLink to="/fields" class="nav-tab" :class="{ 'nav-tab-active': activeTab === 'fields' }">
          <Sprout :size="16" /> Mis campos
        </RouterLink>
        <RouterLink to="/demo" class="nav-tab" :class="{ 'nav-tab-active': activeTab === 'demo' }">
          <FlaskConical :size="16" /> Demo
        </RouterLink>
        <RouterLink v-if="isAdmin" to="/admin/fields" class="nav-tab" :class="{ 'nav-tab-active': activeTab === 'admin' }">
          <Shield :size="16" /> Admin
        </RouterLink>
      </div>

      <div class="flex items-center gap-3">
        <RouterLink to="/account" class="flex items-center gap-2 pr-3 pl-1 py-1 rounded-full bg-chip">
          <span class="w-7 h-7 rounded-full bg-primary-soft text-primary text-xs font-bold flex items-center justify-center">
            {{ user?.email?.[0]?.toUpperCase() || 'U' }}
          </span>
          <span class="text-[13px] font-semibold">Cuenta</span>
        </RouterLink>
      </div>
    </nav>

    <!-- ─── Mobile brand bar ─── -->
    <nav v-if="isAuthenticated" class="md:hidden bg-paper px-5 pt-3 pb-2 flex items-center justify-between">
      <div class="flex items-center gap-2 text-primary">
        <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
          <path d="M16 3c-4 6-7 9-7 13a7 7 0 0 0 14 0c0-4-3-7-7-13z" fill="currentColor"/>
        </svg>
        <span class="text-base font-bold tracking-tight text-ink">Irrigation Advisor</span>
      </div>
    </nav>

    <!-- ─── Unauthenticated top bar (login/register) ─── -->
    <nav v-else class="bg-paper px-5 md:px-8 py-3 flex items-center justify-between">
      <div class="flex items-center gap-2 text-primary">
        <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
          <path d="M16 3c-4 6-7 9-7 13a7 7 0 0 0 14 0c0-4-3-7-7-13z" fill="currentColor"/>
        </svg>
        <span class="text-base md:text-lg font-bold tracking-tight text-ink">Irrigation Advisor</span>
      </div>
      <div class="flex gap-2 text-sm">
        <RouterLink to="/login" class="px-3 py-1.5 text-muted font-semibold">Ingresar</RouterLink>
        <RouterLink to="/register" class="px-3 py-1.5 bg-primary text-white rounded-xl font-semibold">Registrarse</RouterLink>
      </div>
    </nav>

    <main class="flex-1 pb-20 md:pb-0">
      <RouterView />
    </main>

    <!-- ─── Mobile bottom tab bar ─── -->
    <nav v-if="isAuthenticated" class="md:hidden fixed bottom-0 inset-x-0 bg-surface border-t border-line pt-2.5 pb-1.5 px-2 flex justify-around z-40">
      <RouterLink to="/" class="tab-item" :class="{ 'tab-item-active': activeTab === 'home' }">
        <Home :size="22" />
        <span>Inicio</span>
      </RouterLink>
      <RouterLink to="/fields" class="tab-item" :class="{ 'tab-item-active': activeTab === 'fields' }">
        <Sprout :size="22" />
        <span>Campos</span>
      </RouterLink>
      <RouterLink v-if="isAdmin" to="/admin/fields" class="tab-item" :class="{ 'tab-item-active': activeTab === 'admin' }">
        <Shield :size="22" />
        <span>Admin</span>
      </RouterLink>
      <RouterLink to="/demo" class="tab-item" :class="{ 'tab-item-active': activeTab === 'demo' }">
        <FlaskConical :size="22" />
        <span>Demo</span>
      </RouterLink>
      <RouterLink to="/account" class="tab-item" :class="{ 'tab-item-active': activeTab === 'account' }">
        <User :size="22" />
        <span>Cuenta</span>
      </RouterLink>
    </nav>

    <InstallPrompt />
  </div>
</template>

<style scoped>
.nav-tab {
  display: flex; align-items: center; gap: 7px;
  padding: 8px 14px; border-radius: 10px;
  font-size: 14px; font-weight: 600;
  color: var(--color-muted);
}
.nav-tab-active {
  background: var(--color-chip);
  color: var(--color-ink);
}

.tab-item {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  padding: 4px 12px;
  color: var(--color-soft);
}
.tab-item span {
  font-size: 10px; font-weight: 700; letter-spacing: 0.3px;
  text-transform: uppercase;
}
.tab-item-active { color: var(--color-primary); }
</style>

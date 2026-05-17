<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import { requestPushPermission, subscribeToPush } from '../services/push'
import { Bell, BellOff, ArrowRight, AlertCircle} from 'lucide-vue-next'


const router = useRouter()
const { user, logout } = useAuth()

const pushStatus = ref('idle') // idle | requesting | granted | denied | unsupported | error

async function syncSubscription() {
    // Solo marca 'granted' si la suscripcion se sincronizo de verdad con el backend.
    try {
        await subscribeToPush()
        pushStatus.value = 'granted'
    } catch (e) {
        console.error('Error al sincronizar la subscripcion push:', e)
        pushStatus.value = 'error'
    }
}

async function setupPushNotifications() {
    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
        pushStatus.value = 'unsupported'
        return
    }
    if (Notification.permission === 'granted') {
        await syncSubscription()
        return
    }
    if (Notification.permission === 'denied') {
        pushStatus.value = 'denied'
        return
    }
    pushStatus.value = 'idle'
}

async function enableNotifications() {
    pushStatus.value = 'requesting'
    const granted = await requestPushPermission()
    if (!granted) {
        pushStatus.value = 'denied'
        return
    }
    await syncSubscription()
}

function handleLogout() {
    logout()
    router.push('/login')
}

onMounted(setupPushNotifications)
</script>

<template>
    <div class="max-w-2xl lg:max-w-3xl mx-auto px-4 py-6 space-y-4">

    <!-- Bienvenida -->
    <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-4">
      <p class="text-xs text-gray-400 mb-0.5">Bienvenido</p>
      <p class="font-bold text-gray-900 text-base">{{ user?.email }}</p>
    </div>

    <!-- Banner push: idle -->
    <div
      v-if="pushStatus === 'idle'"
      class="bg-amber-50 border-2 border-amber-400 rounded-2xl p-4"
    >
      <div class="flex items-start gap-3 mb-3">
        <Bell class="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
        <div>
          <p class="font-bold text-amber-900 text-sm">Activá las notificaciones</p>
          <p class="text-amber-800 text-xs mt-0.5">Recibí alertas de riego en el momento justo.</p>
        </div>
      </div>
      <button
        @click="enableNotifications"
        class="w-full bg-amber-500 hover:bg-amber-600 text-white font-bold py-2.5 rounded-xl text-sm transition-colors"
      >
        Activar notificaciones
      </button>
    </div>

    <!-- Banner push: requesting -->
    <div
      v-else-if="pushStatus === 'requesting'"
      class="bg-amber-50 border-2 border-amber-300 rounded-2xl p-4 flex items-center gap-3"
    >
      <Bell class="w-5 h-5 text-amber-500 shrink-0" />
      <p class="text-amber-800 text-sm font-medium">Esperando permiso...</p>
    </div>

    <!-- Banner push: denied -->
    <div
      v-else-if="pushStatus === 'denied'"
      class="bg-gray-100 border border-gray-200 rounded-2xl p-4 flex items-center gap-3"
    >
      <BellOff class="w-5 h-5 text-gray-400 shrink-0" />
      <p class="text-gray-500 text-sm">Notificaciones desactivadas. Habilitálas desde la configuración del navegador.</p>
    </div>

    <!-- Banner push: error -->
    <div
      v-else-if="pushStatus === 'error'"
      class="bg-red-50 border-2 border-red-300 rounded-2xl p-4"
    >
      <div class="flex items-start gap-3 mb-3">
        <AlertCircle class="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
        <div>
          <p class="font-bold text-red-800 text-sm">No se pudieron activar las notificaciones</p>
          <p class="text-red-600 text-xs mt-0.5">Verificá tu conexión e intentá de nuevo.</p>
        </div>
      </div>
      <button
        @click="enableNotifications"
        class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 rounded-xl text-sm transition-colors"
      >
        Reintentar
      </button>
    </div>

    <!-- CTA principal -->
    <RouterLink
      to="/fields"
      class="flex items-center justify-between bg-green-800 hover:bg-green-700 text-white font-bold py-4 px-5 rounded-2xl text-base transition-colors shadow-sm"
    >
      <span>Ver mis campos</span>
      <ArrowRight class="w-5 h-5" />
    </RouterLink>

  </div>
</template>

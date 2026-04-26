<script setup>
import {ref, onMounted} from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import { useAuth } from '../stores/auth'
import { requestPushPermission, subscribeToPush } from '../services/push'


const router = useRouter()
const { user, logout } = useAuth()

const pushStatus = ref('idle') // idle | requesting | granted | denied | unsupported

async function setupPushNotifications() {
    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
        pushStatus.value = 'unsupported'
        return
    }
    if (Notification.permission === 'granted') {
        pushStatus.value = 'granted'
        await subscribeToPush()
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
    if (granted) {
        await subscribeToPush()
        pushStatus.value = 'granted'
    } else {
        pushStatus.value = 'denied'
    }
}

function handleLogout() {
    logout()
    router.push('/login')
}

onMounted(async () => {
    console.log('VAPID KEY: ', import.meta.env.VITE_VAPID_PUBLIC_KEY)
    setupPushNotifications()
})
</script>

<template>
    <div class="home">
        <header class="home-header">
            <h1>Irrigation Advisor</h1>
        </header>
    
        <p v-if="user">Bienvenido, <strong>{{ user.email }}</strong>.</p>

        <!-- Banner de notificaciones -->
        <div v-if="pushStatus === 'idle'" class="push-banner push-idle">
            <span> Activá las notificaciones para recibir alertas de riego</span>
            <button @click="enableNotifications" class="btn-enable">Activar</button>
        </div>
        <div v-else-if="pushStatus === 'granted'" class="push-banner push-granted">
            Notificaciones activadas
        </div>
        <div v-else-if="pushStatus === 'denied'" class="push-banner push-denied">
            Notificaciones desactivadas. Activalas desde la configuracion del browser.
        </div>

        <div class="actions">
            <RouterLink to="/fields" class="btn-primary">Ver mis campos</RouterLink>
        </div>
    </div>
</template>

<style scoped>
.home {
    max-width: 600px;
    margin: 0 auto;
    padding: 1rem;
}
.home-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}
.home-header h1 { margin: 0; font-size: 1.4rem; color: #2e7d32; }
.btn-logout {
    background: none;
    border: 1px solid #ccc;
    padding: 0.3rem 0.8rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
}
.push-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
}
.push-idle    { background: #fff3cd; color: #856404; }
.push-granted { background: #d4edda; color: #155724; }
.push-denied  { background: #f8d7da; color: #721c24; }
.btn-enable {
    background: #2e7d32;
    color: white;
    border: none;
    padding: 0.3rem 0.8rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
}
.actions { margin-top: 1rem; }
.btn-primary {
    display: inline-block;
    padding: 0.6rem 1.2rem;
    background: #2e7d32;
    color: white;
    text-decoration: none;
    border-radius: 6px;
}
</style>
import api from './api'
import { urlBase64ToUint8Array, idbSet, ENDPOINT_KEY } from './push-shared'


export async function requestPushPermission() {
    if (!('Notification' in window) || !('serviceWorker' in navigator)) return false
    const permission = await Notification.requestPermission()
    return permission === 'granted'
}

export async function subscribeToPush() {
    const reg = await navigator.serviceWorker.ready

    let sub = await reg.pushManager.getSubscription()
    if (!sub) {
        sub = await reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(import.meta.env.VITE_VAPID_PUBLIC_KEY),
        })
    }
    await sendSubscriptionToServer(sub)
    return sub
}

async function sendSubscriptionToServer(sub) {
    const keys = sub.toJSON().keys
    await api.post('/push/subscribe', {
        endpoint: sub.endpoint,
        p256dh: keys.p256dh,
        auth: keys.auth
    })
    // Guardamos el endpoint para que el service worker pueda migrarlo si rota.
    await idbSet(ENDPOINT_KEY, sub.endpoint).catch(
        (e) => console.warn('No se pudo guardar el endpoint en IndexedDB', e)
    )
}

export async function unsubscribeFromPush() {
    const reg = await navigator.serviceWorker.ready
    const sub = await reg.pushManager.getSubscription()
    if (!sub) return
    const keys = sub.toJSON().keys
    await api.delete('/push/subscribe', {
        data: {
            endpoint: sub.endpoint,
            p256dh: keys.p256dh,
            auth: keys.auth
        },
    })
    await sub.unsubscribe()
}
import api from './api'

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4)
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

export async function requestPushPermission() {
    if (!('Notification' in window) || !('serviceWorker' in navigator)) return false

    const permission = await Notification.requestPermission()
    return permission === 'granted'
}

export async function subscribeToPush() {
    const reg = await navigator.serviceWorker.ready

    const existing = await reg.pushManager.getSubscription()
    if (existing) {
        await sendSubscriptionToServer(existing)
        return existing
    }

    const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(import.meta.env.VITE_VAPID_PUBLIC_KEY),
    })

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
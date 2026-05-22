import { precacheAndRoute } from 'workbox-precaching';
import { clientsClaim } from 'workbox-core';
import { urlBase64ToUint8Array, idbGet, idbSet, ENDPOINT_KEY } from './services/push-shared';


self.skipWaiting();
clientsClaim();

precacheAndRoute(self.__WB_MANIFEST);

// Manejo de notificaciones push entrantes
self.addEventListener('push', (event) => {
    if (!event.data) return
    const data = event.data.json()
    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: '/favicon.svg',
            tag: 'irrigation-advisor',
            renotify: true
        })
    )
})

// Click en notificacion: abre la app
self.addEventListener('notificationclick', (event) => {
    event.notification.close()
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(windowClients => {
            for (const client of windowClients) {
                if ('focus' in client) return client.focus()
            }
            if (clients.openWindow) return clients.openWindow('/')
        })
    )
})

// Renovacion: el navegador rota la suscripcion periodicamente, incluso con la app cerrada.
self.addEventListener('pushsubscriptionchange', (event) => {
    event.waitUntil(renewSubscription())
})

async function renewSubscription() {
    const oldEndpoint = await idbGet(ENDPOINT_KEY)
    if (!oldEndpoint) return 

    const sub = await self.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(import.meta.env.VITE_VAPID_PUBLIC_KEY),
    })
    const keys = sub.toJSON().keys
    
    const res = await fetch(`${import.meta.env.VITE_API_URL}/push/migrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_endpoint: oldEndpoint, endpoint: sub.endpoint, p256dh: keys.p256dh, auth: keys.auth }),
    })
    if (res.ok) {
        await idbSet(ENDPOINT_KEY, sub.endpoint)
    }
}
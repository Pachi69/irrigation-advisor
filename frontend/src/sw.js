import { precacheAndRoute } from 'workbox-precaching';

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
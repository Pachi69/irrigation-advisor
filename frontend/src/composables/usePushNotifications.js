import { ref, onMounted } from 'vue'
import { requestPushPermission, subscribeToPush } from '../services/push'

export function usePushNotifications() {
    const pushStatus = ref('idle')

    async function enableNotifications() {
        pushStatus.value = 'requesting'
        const granted = await requestPushPermission()
        if (!granted) { pushStatus.value = 'denied'; return }
        try { await subscribeToPush(); pushStatus.value = 'granted' }
        catch { pushStatus.value = 'error' }
    }

    onMounted(() => {
        if ('Notification' in window) {
            if (Notification.permission === 'granted') pushStatus.value = 'granted'
            else if (Notification.permission === 'denied') pushStatus.value = 'denied'
        }
    })

    return { pushStatus, enableNotifications }
}
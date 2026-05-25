<script setup>
import { ref, onMounted } from 'vue'
import { Download } from 'lucide-vue-next'


const deferredPrompt = ref(null)
const visible = ref(false)

onMounted(() => {
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault()
        deferredPrompt.value = e
        visible.value = true
    })
    window.addEventListener('appinstalled', () => {
        visible.value = false
        deferredPrompt.value = null
    })
})

async function install() {
    if (!deferredPrompt.value) return
    deferredPrompt.value.prompt()
    await deferredPrompt.value.userChoice
    deferredPrompt.value = null
    visible.value = false
}
</script>

<template>
    <button
        v-if="visible"
        @click="install"
        aria-label="Instalar app"
        class="fixed bottom-4 right-4 z-50 flex items-center gap-2 bg-green-800 hover:bg-green-700 text-white font-bold px-4 py-3 rounded-2xl shadow-lg transition-colors"
    >
        <Download class="w-5 h-5" />
    </button>
</template>
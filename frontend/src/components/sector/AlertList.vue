<script setup>
import { AlertTriangle, Snowflake, Sun } from 'lucide-vue-next'
import { ALERT_LABELS } from '../../utils/labels.js'

defineProps({ alerts: { type: Array, default: () => [] } })
const emit = defineEmits(['dismiss'])

const alertIcon = { frost: Snowflake, heat_wave: Sun }

function formatAlertDate(dateStr) {
    const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1)
    const d = new Date(dateStr + 'T00:00:00')
    if (d.toDateString() === tomorrow.toDateString()) return 'mañana'
    return d.toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
}
</script>

<template>
    <div v-for="a in alerts" :key="a.id" class="bg-frost text-white rounded-2xl px-4 py-3 flex items-center gap-3">
        <div class="w-9 h-9 rounded-full bg-water/30 flex items-center justify-center shrink-0">
            <component :is="alertIcon[a.type] || AlertTriangle" :size="18" />
        </div>
        <div class="flex-1">
            <div class="text-[10px] font-bold uppercase tracking-wider opacity-75">Alerta climática</div>
            <div class="text-sm font-semibold">{{ ALERT_LABELS[a.type] }} · {{ formatAlertDate(a.date) }}</div>
        </div>
        <button @click="emit('dismiss', a.id)" class="w-6 h-6 rounded-full bg-white/10 text-white/70 flex items-center
    justify-center text-sm">×</button>
    </div>
</template>
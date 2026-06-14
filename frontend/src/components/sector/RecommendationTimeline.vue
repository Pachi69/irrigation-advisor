<script setup>
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

defineProps({
    dates: { type: Array, required: true },
    loadingDate: { type: Boolean, default: false },
    isLatest: { type: Boolean, default: false },
    label: { type: String, default: '' },
})
const selectedIndex = defineModel('index', { type: Number, default: 0 })
const emit = defineEmits(['step', 'change'])

function shortDate(iso) {
    if (!iso) return ''
    return new Date(iso + 'T00:00:00').toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })
}
</script>

<template>
    <div class="bg-surface border border-line rounded-2xl px-4 md:px-6 py-4 mt-4 md:mt-5">
        <div class="flex items-center justify-between mb-3">
            <span class="app-label">Línea de tiempo</span>
            <span class="app-mono text-xs font-bold text-ink">
                {{ isLatest ? 'Hoy' : label }}
                <span class="text-muted font-normal"> · {{ selectedIndex + 1 }} / {{ dates.length }}</span>
            </span>
        </div>
        <div class="flex items-center gap-3">
            <button @click="emit('step', -1)" :disabled="loadingDate || selectedIndex === 0"
                    class="w-9 h-9 shrink-0 rounded-xl border border-line bg-surface flex items-center justify-center text-ink disabled:opacity-30 disabled:cursor-not-allowed">
                <ChevronLeft :size="18" />
            </button>
            <input type="range" min="0" :max="dates.length - 1" step="1"
                    v-model.number="selectedIndex" @change="emit('change')" :disabled="loadingDate"
                    class="flex-1 accent-primary disabled:opacity-50" />
            <button @click="emit('step', 1)" :disabled="loadingDate || isLatest"
                    class="w-9 h-9 shrink-0 rounded-xl border border-line bg-surface flex items-center justify-center text-ink disabled:opacity-30 disabled:cursor-not-allowed">
                <ChevronRight :size="18" />
            </button>
        </div>
        <div class="flex justify-between mt-2">
            <span class="app-label">{{ shortDate(dates[0]) }}</span>
            <span class="app-label">{{ shortDate(dates[dates.length - 1]) }}</span>
        </div>
    </div>
</template>
<script setup>
import { URGENCY_LABEL } from '../../utils/labels'

defineProps({
    segments: { type: Array, default: () => [] },
})

const URG = {
    low:      { dot: 'var(--color-primary)' },
    medium:   { dot: 'var(--color-amber)' },
    high:     { dot: '#D8651C' },
    critical: { dot: 'var(--color-rust)' },
}
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3">Distribución de urgencia</div>
        <div class="flex h-3 rounded-full overflow-hidden bg-chip">
            <div v-for="seg in segments" :key="seg.key" :style="{ width: seg.w + '%', background: URG[seg.key].dot }"></div>
        </div>
        <div class="flex flex-wrap gap-x-4 gap-y-1.5 mt-3">
            <div v-for="seg in segments" :key="seg.key" class="flex items-center gap-1.5 text-xs">
                <span class="w-2 h-2 rounded-full" :style="{ background: URG[seg.key].dot }"></span>
                <span class="text-muted">{{ URGENCY_LABEL[seg.key] }}</span>
                <span class="app-mono font-bold text-ink">{{ seg.n }}</span>
            </div>
        </div>
    </div>
</template>
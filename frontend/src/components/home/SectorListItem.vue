<script setup>
import { RouterLink } from 'vue-router'
import { CROP_LABELS } from '../../utils/labels'
import { irrigationAmount } from '../../utils/format'
import Sparkline from '../Sparkline.vue'

defineProps({
    sector: { type: Object, required: true },
})

function urgencyDot(u) {
    return {
        critical: 'bg-rust', high: 'bg-amber',
        medium: 'bg-amber', low: 'bg-primary', none: 'bg-soft',
    }[u] || 'bg-soft'
}

function urgencyColor(u) {
    return {
        critical: 'var(--color-rust)', high: 'var(--color-rust)',
        medium: 'var(--color-amber)', low: 'var(--color-primary)', none: 'var(--color-soft)',
    }[u] || 'var(--color-primary)'
}
</script>

<template>
    <RouterLink
        :to="`/sectors/${sector.id}/recommendation`"
        class="bg-surface border border-line rounded-2xl p-4 md:p-5 flex items-center gap-3 hover:border-soft transition-colors"
    >
        <span
            class="w-2 h-2 rounded-full shrink-0"
            :class="urgencyDot(sector.last_recommendation?.urgency || 'none')"
        />
        <div class="flex-1 min-w-0">
            <div class="text-[15px] md:text-base font-bold text-ink tracking-tight truncate">{{ sector.fieldName }} · {{ sector.name }}</div>
            <div class="text-xs text-muted">{{ CROP_LABELS[sector.crop_type] || sector.crop_type }} · {{ sector.area_ha?.toFixed(1) }} ha</div>
        </div>
        <Sparkline
            v-if="sector.last_recommendation?.deficit_history?.length > 1"
            :data="sector.last_recommendation.deficit_history"
            :color="urgencyColor(sector.last_recommendation.urgency)"
            :width="60" :height="24"
        />
        <div class="app-mono text-base font-bold text-ink min-w-[60px] text-right">
            <template v-if="sector.last_recommendation && sector.last_recommendation.recommended_irrigation_mm > 0">
                {{ irrigationAmount(sector.last_recommendation) }}
            </template>
            <template v-else-if="sector.last_recommendation">—</template>
            <span v-else class="text-xs text-muted font-normal">Sin datos</span>
        </div>
    </RouterLink>
</template>
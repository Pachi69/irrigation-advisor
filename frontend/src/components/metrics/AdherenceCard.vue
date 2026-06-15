<script setup>
import { CheckCircle2 } from 'lucide-vue-next'
import { pct } from '../../utils/format'

defineProps({
    adherence: { type: Object, required: true },
})
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3 flex items-center gap-1.5"><CheckCircle2 :size="13" /> Adherencia</div>
        <div class="app-display text-4xl text-ink">{{ pct(adherence.adherence_pct) }}</div>
        <p class="text-sm text-muted mt-1.5 leading-relaxed">
            {{ adherence.confirmed }} de {{ adherence.actionable }} riegos recomendados
            confirmados · {{ adherence.pending }} pendientes.
        </p>
    </div>
</template>
<script setup>
import { n1, n2 } from '../../utils/format'

defineProps({
    verdict: { type: Object, required: true },
})
</script>

<template>
    <div class="bg-primary text-primary-ink rounded-3xl p-5 md:p-6">
        <div class="text-[11px] font-bold uppercase tracking-wider opacity-80">Salud hídrica del periodo</div>
        <div class="flex items-end gap-2 mt-1.5">
            <span class="app-display text-5xl">{{ verdict.coverage != null ? verdict.coverage + '%' : '—' }}</span>
            <span class="text-base opacity-85 mb-1.5">de su demanda hídrica cubierta</span>
        </div>
        <p class="text-sm opacity-85 mt-2 leading-relaxed">
            Ks promedio {{  n2(verdict.ks) }} ·
            Percolación: <strong>{{ n1(verdict.perc) }} mm</strong> ·
            Estrés: <strong>{{ verdict.stressDays }}/{{ verdict.days }} días</strong>.
        </p>
    </div>
</template>

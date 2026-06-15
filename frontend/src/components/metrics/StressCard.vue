<script setup>
import { AlertTriangle } from 'lucide-vue-next'
import { n1, n2, pct } from '../../utils/format'

defineProps({
    stress: { type: Object, required: true },
})
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3 flex items-center gap-1.5"><AlertTriangle :size="13" /> Estrés hídrico</div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
            <div>
                <div class="app-label">Días en estrés (Ks&lt;1)</div>
                <div class="app-mono text-base font-bold mt-0.5 text-rust">{{ stress.stress_days }}
                    <span class="text-sm text-muted font-semibold">/{{ stress.days_evaluated }}</span>
                </div>
                <div class="app-mono text-xs text-muted">{{ pct(stress.stress_days_pct) }}</div>
            </div>
            <div>
                <div class="app-label">Severo (Ks&lt;0.5)</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ stress.severe_stress_days }} 
                    <span class="text-sm text-muted font-semibold">d</span>
                </div>
            </div>
            <div>
                <div class="app-label">Ks promedio</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ n2(stress.avg_ks) }}</div>
                <div class="app-mono text-xs text-muted">mín {{ n2(stress.min_ks) }}</div>
            </div>
            <div>
                <div class="app-label">Déficit prom</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ n1(stress.avg_deficit_mm) }} 
                    <span class="text-sm text-muted font-semibold">mm</span>
                </div>
                <div class="app-mono text-xs text-muted">{{ pct(stress.avg_deficit_pct) }} TAW</div>
            </div>
        </div>
    </div>
</template>
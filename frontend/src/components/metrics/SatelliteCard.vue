<script setup>
import { Satellite } from 'lucide-vue-next'
import { n2, pct } from '../../utils/format'

defineProps({
    satellite: { type: Object, required: true },
})
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3 flex items-center gap-1.5"><Satellite :size="13" /> Cobertura satelital</div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
            <div>
                <div class="app-label">Días con Kc satelital</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ satellite.s2_dynamic_days }}
                    <span class="text-sm text-muted font-semibold">/{{ satellite.days_evaluated }}</span>
                </div>
                <div class="app-mono text-xs text-muted">{{ pct(satellite.s2_dynamic_pct) }}</div>
            </div>
            <div>
                <div class="app-label">NDVI prom</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ n2(satellite.avg_ndvi) }}</div>
                <div class="app-mono text-xs text-muted">{{ satellite.ndvi_days }} días c/imagen</div>
            </div>
        </div>
    </div>
</template>
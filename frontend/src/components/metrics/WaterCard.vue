<script setup>
import { Droplets } from 'lucide-vue-next'
import { n0, n1, pct } from '../../utils/format'

defineProps({
    water: { type: Object, required: true },
})
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3 flex items-center gap-1.5"><Droplets :size="13" /> Agua del período</div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
            <div>
                <div class="app-label">Consumo neto</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ n1(water.net_requirement_mm) }} 
                    <span class="text-sm text-muted font-semibold">mm</span>
                </div>
                <div class="app-mono text-xs text-muted">ETc − lluvia</div>
            </div>
            <div>
                <div class="app-label">Aplicada</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ n1(water.applied_mm) }} 
                    <span class="text-sm text-muted font-semibold">mm</span>
                </div>
                <div class="app-mono text-xs text-muted">{{ n0(water.applied_m3) }} m³</div>
            </div>
            <div>
                <div class="app-label">Percolación</div>
                <div class="app-mono text-base font-bold mt-0.5 text-rust">{{ n1(water.deep_percolation_mm) }} 
                    <span class="text-sm text-muted font-semibold">mm</span>
                </div>
                <div class="app-mono text-xs text-muted">drenaje profundo</div>
            </div>
            <div>
                <div class="app-label">Aplicado vs consumo</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ pct(water.applied_vs_required_pct) }}</div>
            </div>
        </div>
    </div>
</template>
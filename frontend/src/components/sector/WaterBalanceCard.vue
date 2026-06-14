<script setup>
import { computed } from 'vue'
import SoilTank from '../SoilTank.vue'

const props = defineProps({ rec: { type: Object, required: true } })

const deficitPct = computed(() =>
    Math.min(100, Math.round((props.rec.water_deficit_mm / props.rec.taw_mm) * 100))
)
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3">Balance hídrico</div>
        <SoilTank :deficit-pct="deficitPct" />
        <div class="grid grid-cols-2 gap-x-4 gap-y-3.5 mt-4 pt-4 border-t border-line">
            <div>
                <div class="app-label">Déficit actual <span class="normal-case font-normal tracking-normal">(Dr)</span></div>
                <div class="app-mono text-base font-bold mt-0.5">{{ rec.water_deficit_mm?.toFixed(1) }} <span class="text-sm text-muted font-semibold">mm</span></div>
            </div>
            <div>
                <div class="app-label">TAW <span class="normal-case font-normal tracking-normal">(agua total)</span></div>
                <div class="app-mono text-base font-bold mt-0.5">{{ rec.taw_mm?.toFixed(0) }} <span class="text-sm text-muted font-semibold">mm</span></div>
            </div>
            <div>
                <div class="app-label">RAW <span class="normal-case font-normal tracking-normal">(límite sin estrés)</span></div>
                <div class="app-mono text-base font-bold mt-0.5">{{ rec.raw_mm?.toFixed(0) }} <span class="text-sm text-muted font-semibold">mm</span></div>
            </div>
            <div>
                <div class="app-label">Estrés <span class="normal-case font-normal tracking-normal">(Ks)</span></div>
                <div class="app-mono text-base font-bold mt-0.5">{{ rec.ks?.toFixed(2) }}</div>
            </div>
        </div>
    </div>
</template>
<script setup>
import { STAGE_LABELS, KC_SOURCE_LABELS } from '../../utils/labels.js'

defineProps({ rec: { type: Object, required: true } })
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3">Cultivo · Kc</div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
            <div>
                <div class="app-label">Etapa <span class="normal-case font-normal tracking-normal">(fenológica)</span></div>
                <div class="text-sm font-bold mt-0.5">{{ STAGE_LABELS[rec.phenological_stage] }}</div>
            </div>
            <div>
                <div class="app-label">Kc <span class="normal-case font-normal tracking-normal">(coef. cultivo)</span></div>
                <div class="app-mono text-base font-bold mt-0.5">{{ rec.kc?.toFixed(3) }}</div>
            </div>
            <div>
                <div class="app-label">Fuente Kc</div>
                <div class="text-sm font-bold mt-0.5">{{ KC_SOURCE_LABELS[rec.kc_source] }}</div>
            </div>
            <div>
                <div class="app-label">ETo ayer <span class="normal-case font-normal tracking-normal">(evapotransp.)</span></div>
                <div class="app-mono text-base font-bold mt-0.5">{{ rec.eto_mm?.toFixed(2) }} <span class="text-sm text-muted font-semibold">mm</span></div>
            </div>
        </div>
    </div>
</template>
<script setup>
import { n1 } from '../../utils/format'

defineProps({
    climate: { type: Object, required: true },
})
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3">Clima del período</div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3.5">
            <div>
                <div class="app-label">ETo</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ n1(climate.eto_mm) }} 
                    <span class="text-sm text-muted font-semibold">mm</span>
                </div>
            </div>
            <div>
                <div class="app-label">ETc</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ n1(climate.etc_mm) }} 
                    <span class="text-sm text-muted font-semibold">mm</span>
                </div>
            </div>
            <div>
                <div class="app-label">Lluvia</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ n1(climate.rain_mm) }} 
                    <span class="text-sm text-muted font-semibold">mm</span>
                </div>
            </div>
            <div>
                <div class="app-label">Lluvia efectiva</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ n1(climate.effective_rain_mm) }} 
                    <span class="text-sm text-muted font-semibold">mm</span>
                </div>
            </div>
        </div>
    </div>
</template>
<script setup>
import { computed, toRef, useTemplateRef } from 'vue'
import { Satellite } from 'lucide-vue-next'
import { useNdviMap } from '../../composables/useNdviMap.js'

const props = defineProps({
    sector: { type: Object, required: true },
    rec: { type: Object, required: true },
    satelliteUrl: { type: String, default: null },
})

const mapRef = useTemplateRef('mapRef')
const { overlayOpacity } = useNdviMap(mapRef, toRef(props, 'sector'), toRef(props, 'satelliteUrl'))

const ndviAge = computed(() => {
    if (!props.rec.ndvi_date || !props.rec.date) return null
    return Math.floor((new Date(props.rec.date) - new Date(props.rec.ndvi_date)) / 86_400_000)
})
</script>

<template>
    <div v-if="sector?.polygon_geojson" class="bg-surface border border-line rounded-3xl p-5">
        <div class="flex items-center justify-between mb-3">
            <div class="app-label">Imagen satelital · NDVI</div>
            <span v-if="rec.ndvi_date" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-primary-soft text-primary text-[10px] font-bold uppercase tracking-wider">
                <Satellite :size="11" /> Sentinel-2 · {{ rec.ndvi_date }}
            </span>
        </div>
        <div ref="mapRef" class="w-full h-56 md:h-60 rounded-2xl overflow-hidden mb-3 bg-line/40"></div>

        <div v-if="satelliteUrl" class="flex items-center gap-3 mb-3">
            <span class="app-label w-16">Opacidad</span>
            <input type="range" min="0" max="1" step="0.05" v-model.number="overlayOpacity" class="flex-1 accent-primary" />
            <span class="app-mono text-xs text-muted w-8 text-right">{{ Math.round(overlayOpacity * 100) }}%</span>
        </div>

        <div v-if="satelliteUrl" class="flex items-center gap-2 mb-3.5">
            <span class="app-label">Estrés</span>
            <div class="flex-1 h-1.5 rounded-full" style="background: linear-gradient(to right, #d73027, #fc8d59, #fee08b, #a6d96a,#1a9850)" />
            <span class="app-label">Vigor</span>
        </div>

        <p v-if="rec.ndvi != null && !satelliteUrl" class="text-xs text-muted mb-3">
            Imagen NDVI no disponible para esta fecha; el índice corresponde al {{ rec.ndvi_date }}.
        </p>
        <p v-else-if="rec.ndvi == null" class="text-xs text-muted mb-3">
            Sin datos satelitales para esta fecha; el Kc se calculó por tabla (FAO-56).
        </p>

        <div v-if="satelliteUrl" class="grid grid-cols-3 gap-3 md:gap-4">
            <div>
                <div class="app-label">NDVI</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ rec.ndvi?.toFixed(3) }}</div>
            </div>
            <div>
                <div class="app-label">Nubosidad</div>
                <div class="app-mono text-base font-bold mt-0.5">{{ rec.cloud_cover_pct?.toFixed(0) }}%</div>
            </div>
            <div>
                <div class="app-label">Antigüedad</div>
                <div class="app-mono text-base font-bold mt-0.5" :class="{ 'text-amber': ndviAge > 15 }">{{ ndviAge }} d</div>
            </div>
        </div>
        <p v-if="ndviAge > 15" class="text-xs text-amber mt-3 leading-relaxed">
            La imagen tiene más de 15 días. El Kc se calculó por tabla (FAO-56).
        </p>
    </div>
</template>
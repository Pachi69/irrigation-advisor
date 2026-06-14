<script setup>
import { useRouter, RouterLink } from 'vue-router'
import { ArrowLeft, Clock, Droplet, Pencil, Gauge } from 'lucide-vue-next'
import { CROP_LABELS } from '../../utils/labels.js'

const props = defineProps({
    sector: { type: Object, default: null },
    sectorId: { type: [String, Number], required: true },
})
const router = useRouter()
function goBack() {
    router.push(props.sector ? `/fields/${props.sector.field_id}` : '/fields')
}
</script>

<template>
    <div>
        <!-- Breadcrumb / back row -->
        <div class="flex items-center justify-between mb-4 md:mb-5 gap-2">
            <button @click="goBack" class="flex items-center gap-1.5 text-primary font-semibold text-sm">
                <ArrowLeft :size="16" />
                <span class="hidden md:inline">Volver al campo</span>
                <span class="md:hidden">Volver</span>
            </button>
            <div class="flex items-center gap-2">
                <RouterLink :to="`/sectors/${sectorId}/metrics`" class="flex items-center gap-1 whitespace-nowrap text-xs md:text-sm font-semibold text-ink border border-line bg-surface px-3 py-1.5 rounded-xl">
                    <Gauge :size="13" /> <span class="hidden md:inline">Métricas</span>
                </RouterLink>
                <RouterLink :to="`/sectors/${sectorId}/history`" class="flex items-center gap-1 whitespace-nowrap text-xs md:text-sm font-semibold text-ink border border-line bg-surface px-3 py-1.5 rounded-xl">
                    <Clock :size="13" /> Historial
                </RouterLink>
                <RouterLink :to="`/sectors/${sectorId}/confirmations`" class="flex items-center gap-1 whitespace-nowrap text-xs md:text-sm font-semibold text-primary-ink bg-primary px-3 py-1.5 rounded-xl">
                    <Droplet :size="13" />
                    <span class="md:hidden">Confirmar</span>
                    <span class="hidden md:inline">Confirmar riego</span>
                </RouterLink>
                <RouterLink :to="`/sectors/${sectorId}/edit`" class="flex items-center gap-1 whitespace-nowrap text-xs md:text-sm font-semibold text-ink border border-line bg-surface px-3 py-1.5 rounded-xl">
                    <Pencil :size="13" /> Editar
                </RouterLink>
            </div>
        </div>

        <!-- Title -->
        <h1 v-if="sector" class="text-2xl md:text-3xl font-bold text-ink tracking-tight leading-tight mb-1">
            {{ sector.name }}
        </h1>
        <div v-if="sector" class="text-sm text-muted mb-5 md:mb-6">
            {{ CROP_LABELS[sector.crop_type] || sector.crop_type }}<template v-if="sector.variety"> · {{ sector.variety }}</template> · {{ sector.area_ha?.toFixed(1) }} ha
        </div>
    </div>
</template>
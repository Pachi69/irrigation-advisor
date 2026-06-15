<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { CROP_LABELS } from '../utils/labels'
import { useSectorMetrics } from '../composables/useSectorMetrics'
import HealthHero from '../components/metrics/HealthHero.vue'
import DeficitChart from '../components/metrics/DeficitChart.vue'
import NdviChart from '../components/metrics/NdviChart.vue'
import WaterCard from '../components/metrics/WaterCard.vue'
import StressCard from '../components/metrics/StressCard.vue'
import AdherenceCard from '../components/metrics/AdherenceCard.vue'
import SatelliteCard from '../components/metrics/SatelliteCard.vue'
import UrgencyCard from '../components/metrics/UrgencyCard.vue'
import ClimateCard from '../components/metrics/ClimateCard.vue'
import WeeklyTable from '../components/metrics/WeeklyTable.vue'

const route = useRoute()
const router = useRouter()
const { RANGES, days, data, sector, loading, error, verdict, urgencyBar, setRange } =
    useSectorMetrics(route.params.id)
</script>

<template>
    <div class="max-w-2xl lg:max-w-4xl mx-auto px-4 py-6">

        <div class="flex items-center justify-between mb-1">
            <button
                @click="router.push(`/sectors/${route.params.id}/recommendation`)"
                class="flex items-center gap-1 text-primary font-semibold text-sm hover:underline"
            >
                <ArrowLeft class="w-4 h-4" />
                Recomendación
            </button>
            <h1 class="text-base font-bold text-ink">Evaluación</h1>
            <span class="w-28"></span>
        </div>

        <div class="flex items-center justify-between flex-wrap gap-2 mb-5">
            <div v-if="sector" class="flex items-center gap-2 text-sm">
                <span class="text-muted">{{ sector.name }}</span>
                <span class="px-2 py-0.5 rounded-full bg-chip text-ink text-xs font-semibold">
                    {{ CROP_LABELS[sector.crop_type] || sector.crop_type }}
                </span>
            </div>
            <div class="inline-flex rounded-xl border border-line bg-surface p-0.5">
                <button
                    v-for="d in RANGES" :key="d" @click="setRange(d)"
                    class="px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors"
                    :class="d === days ? 'bg-primary text-primary-ink' : 'text-muted hover:text-ink'"
                >
                    {{ d }} días
                </button>
            </div>
        </div>

        <div v-if="loading" class="text-center py-12 text-soft text-sm">Calculando métricas...</div>
        <div v-else-if="error" class="bg-rust-soft border border-rust/30 text-rust text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>

        <div v-else-if="data" class="flex flex-col gap-3 md:gap-4">
            <HealthHero :verdict="verdict" />
            <DeficitChart :daily="data.daily" :raw-threshold="data.raw_threshold_pct" />
            <NdviChart :series="data.ndvi_series" />

            <div class="grid md:grid-cols-2 gap-3 md:gap-4">
                <WaterCard :water="data.water" />
                <StressCard :stress="data.stress" />
                <AdherenceCard :adherence="data.adherence" />
                <SatelliteCard :satellite="data.satellite" />
            </div>

            <UrgencyCard :segments="urgencyBar" />
            <ClimateCard :climate="data.climate" />
            <WeeklyTable :weekly="data.weekly" />
        </div>
    </div>
</template>
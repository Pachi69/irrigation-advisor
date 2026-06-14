<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSectorRecommendation } from '../composables/useSectorRecommendation.js'
import { CONFIDENCE_LABELS } from '../utils/labels.js'
import UrgencyHero from '../components/UrgencyHero.vue'
import SectorHeader from '../components/sector/SectorHeader.vue'
import AlertList from '../components/sector/AlertList.vue'
import NdviCard from '../components/sector/NdviCard.vue'
import WaterBalanceCard from '../components/sector/WaterBalanceCard.vue'
import CropKcCard from '../components/sector/CropKcCard.vue'
import ClimateCard from '../components/sector/ClimateCard.vue'
import ConfirmCta from '../components/sector/ConfirmCta.vue'
import RecommendationTimeline from '../components/sector/RecommendationTimeline.vue'

const route = useRoute()

const {
  rec, sector, alerts, loading, error, satelliteUrl,
  dates, selectedIndex, loadingDate, isLatest, selectedDate,
  load, loadDate, stepDate, dismissAlert,
} = useSectorRecommendation(route.params.id)

const dateLabel = computed(() => {
  if (!rec.value?.date) return ''
  return new Date(rec.value.date + 'T00:00:00')
    .toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
})
const heroDateLabel = computed(() => (isLatest.value ? `Hoy · ${dateLabel.value}` : dateLabel.value))
const stepperDateLabel = computed(() => {
  if (!selectedDate.value) return ''
  return new Date(selectedDate.value + 'T00:00:00')
    .toLocaleDateString('es-AR', { weekday: 'short', day: 'numeric', month: 'short' })
})

onMounted(load)
</script>

<template>
  <div class="max-w-[1180px] mx-auto px-4 md:px-8 pt-2 md:pt-6 pb-8">

    <SectorHeader :sector="sector" :sector-id="route.params.id" />

    <div v-if="loading" class="text-center py-12 text-muted text-sm">Calculando recomendación...</div>
    <div v-else-if="error" class="bg-rust-soft border border-rust/20 text-rust text-sm font-medium px-4 py-3 rounded-2xl">{{ error }}</div>

    <!-- Main grid -->
    <div v-else-if="rec" class="relative grid md:grid-cols-[1.3fr_1fr] gap-3 md:gap-4" :class="{ 'pointer-events-none': loadingDate }">

      <!-- Velo de carga -->
      <div v-if="loadingDate" class="absolute inset-0 z-[2000] flex items-center justify-center bg-surface/70 backdrop-blur-sm rounded-3xl">
        <span class="text-sm font-semibold text-muted">Cargando {{ stepperDateLabel }}...</span>
      </div>

      <!-- Left column -->
      <div class="flex flex-col gap-3 md:gap-4">
        <UrgencyHero
          :mm="rec.recommended_irrigation_mm"
          :time-min="rec.time_min"
          :volume-m3="rec.volume_m3"
          :urgency="rec.urgency_level"
          :reason="rec.reason"
          :date-label="heroDateLabel"
          :confidence="CONFIDENCE_LABELS[rec.confidence] || 'Sin datos'"
        />
        <AlertList :alerts="alerts" @dismiss="dismissAlert" />
        <NdviCard :sector="sector" :rec="rec" :satellite-url="satelliteUrl" />
      </div>

      <!-- Right column -->
      <div class="flex flex-col gap-3 md:gap-4">
        <WaterBalanceCard :rec="rec" />
        <CropKcCard :rec="rec" />
        <ClimateCard v-if="rec.temp_mean_c != null" :rec="rec" />
        <ConfirmCta :sector-id="route.params.id" />
      </div>
    </div>

    <!-- TIMELINE -->
    <RecommendationTimeline
      v-if="dates.length > 1"
      v-model:index="selectedIndex"
      :dates="dates"
      :loading-date="loadingDate"
      :is-latest="isLatest"
      :label="stepperDateLabel"
      @step="stepDate"
      @change="loadDate"
    />
  </div>
</template>
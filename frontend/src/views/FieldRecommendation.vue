<script setup>
/**
 * FieldRecommendation.vue — pantalla central del producto.
 *
 * Layout:
 *  - Mobile: stack vertical (hero + alertas + balance + cultivo + satélite + acciones).
 *  - Desktop: 2 columnas (hero+alerta+satélite | balance+cultivo+CTA confirm).
 *
 * Reemplaza la versión actual con el mismo flujo de datos (getRecommendation,
 * getFieldAlerts, getFieldSatelliteImage, getFieldById).
 */
import { ref, onMounted, computed, watch, onBeforeUnmount, useTemplateRef } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import {
  getRecommendation, getFieldAlerts, getFieldSatelliteImage, getFieldById,
} from '../services/fields'
import {
  ArrowLeft, Clock, Droplet, Droplets, Leaf, Satellite, AlertTriangle,
  Snowflake, Sun, MoreHorizontal, Pencil,
} from 'lucide-vue-next'
import {
  ALERT_LABELS, STAGE_LABELS, KC_SOURCE_LABELS, CONFIDENCE_LABELS, CROP_LABELS,
} from '../utils/labels'
import UrgencyHero from '../components/UrgencyHero.vue'
import SoilTank from '../components/SoilTank.vue'

const route = useRoute()
const router = useRouter()

const rec = ref(null)
const field = ref(null)
const alerts = ref([])
const loading = ref(true)
const error = ref('')

const satelliteUrl = ref(null)
const mapRef = useTemplateRef('mapRef')
let map = null
let overlayLayer = null
const overlayOpacity = ref(0.8)

const dismissed = JSON.parse(localStorage.getItem('dismissedAlerts') || '[]')

const dateLabel = computed(() => {
  if (!rec.value?.date) return ''
  const d = new Date(rec.value.date + 'T00:00:00')
  return d.toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
})

const deficitPct = computed(() => {
  if (!rec.value) return 0
  return Math.min(100, Math.round((rec.value.water_deficit_mm / rec.value.taw_mm) * 100))
})

const ndviAge = computed(() => {
  if (!rec.value?.ndvi_date) return null
  return Math.floor((new Date() - new Date(rec.value.ndvi_date)) / 86_400_000)
})

const alertIcon = { frost: Snowflake, heat_wave: Sun }

function formatAlertDate(dateStr) {
  const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1)
  const d = new Date(dateStr + 'T00:00:00')
  if (d.toDateString() === tomorrow.toDateString()) return 'mañana'
  return d.toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
}

function dismissAlert(id) {
  const updated = [...dismissed, id]
  localStorage.setItem('dismissedAlerts', JSON.stringify(updated))
  alerts.value = alerts.value.filter(a => a.id !== id)
}

async function load() {
  try {
    [rec.value, field.value] = await Promise.all([
      getRecommendation(route.params.id),
      getFieldById(route.params.id),
    ])
    loadSatellite()
    fetchAlerts()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'No se pudo obtener la recomendación'
  } finally {
    loading.value = false
  }
}

async function fetchAlerts() {
  try {
    const all = await getFieldAlerts(route.params.id)
    alerts.value = all.filter(a => !dismissed.includes(a.id))
  } catch {}
}

async function loadSatellite() {
  try {
    const blob = await getFieldSatelliteImage(route.params.id)
    satelliteUrl.value = URL.createObjectURL(blob)
  } catch {}
}

// Init Leaflet map once we have data + image
watch([satelliteUrl, field], ([url, f]) => {
  if (!url || !f?.polygon_geojson || !mapRef.value || map) return
  const coords = f.polygon_geojson.coordinates[0]
  const lats = coords.map(c => c[1])
  const lngs = coords.map(c => c[0])
  const bounds = [[Math.min(...lats), Math.min(...lngs)], [Math.max(...lats), Math.max(...lngs)]]
  map = L.map(mapRef.value, { zoomControl: false, attributionControl: false })
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}').addTo(map)
  overlayLayer = L.imageOverlay(url, bounds, { opacity: overlayOpacity.value }).addTo(map)
  L.polygon(coords.map(c => [c[1], c[0]]), { color: 'white', weight: 2, fill: false }).addTo(map)
  map.fitBounds(bounds, { padding: [10, 10] })
  setTimeout(() => map?.invalidateSize(), 100)
}, { flush: 'post' })

watch(overlayOpacity, v => overlayLayer?.setOpacity(v))

onBeforeUnmount(() => { map?.remove(); map = null; overlayLayer = null })
onMounted(load)
</script>

<template>
  <div class="max-w-[1180px] mx-auto px-4 md:px-8 pt-2 md:pt-6 pb-8">

    <!-- Breadcrumb / back row -->
    <div class="flex items-center justify-between mb-4 md:mb-5 gap-2">
      <button @click="router.push('/fields')" class="flex items-center gap-1.5 text-primary font-semibold text-sm">
        <ArrowLeft :size="16" />
        <span class="hidden md:inline">Mis campos</span>
        <span class="md:hidden">Volver</span>
      </button>
      <div class="flex items-center gap-2">
        <RouterLink :to="`/fields/${route.params.id}/history`" class="flex items-center gap-1 text-xs md:text-sm font-semibold text-ink border border-line bg-surface px-3 py-1.5 rounded-xl">
          <Clock :size="13" /> Historial
        </RouterLink>
        <RouterLink :to="`/fields/${route.params.id}/confirmations`" class="flex items-center gap-1 text-xs md:text-sm font-semibold text-primary-ink bg-primary px-3 py-1.5 rounded-xl">
          <Droplet :size="13" /> Confirmar riego
        </RouterLink>
        <RouterLink :to="`/fields/${route.params.id}/edit`" class="flex items-center gap-1 text-xs md:text-sm font-semibold text-ink border border-line bg-surface px-3 py-1.5 rounded-xl">
            <Pencil :size="13" /> Editar
        </RouterLink>
      </div>
    </div>

    <!-- Title -->
    <h1 v-if="field" class="text-2xl md:text-3xl font-bold text-ink tracking-tight leading-tight mb-1">
      {{ field.name }}
    </h1>
    <div v-if="field" class="text-sm text-muted mb-5 md:mb-6">
      {{ CROP_LABELS[field.crop_type] || field.crop_type }} · {{ field.area_ha?.toFixed(1) }} ha
    </div>

    <div v-if="loading" class="text-center py-12 text-muted text-sm">Calculando recomendación...</div>
    <div v-else-if="error" class="bg-rust-soft border border-rust/20 text-rust text-sm font-medium px-4 py-3 rounded-2xl">{{ error }}</div>

    <!-- Main grid -->
    <div v-else-if="rec" class="grid md:grid-cols-[1.3fr_1fr] gap-3 md:gap-4">

      <!-- Left column: hero + alerts + satellite -->
      <div class="flex flex-col gap-3 md:gap-4">

        <!-- ─── HERO ─── -->
        <UrgencyHero
          :mm="rec.recommended_irrigation_mm"
          :urgency="rec.urgency_level"
          :reason="rec.reason"
          :date-label="`Hoy · ${dateLabel}`"
          :confidence="CONFIDENCE_LABELS[rec.confidence] || 'Sin datos'"
          :area-ha="field?.area_ha || 1"
        />

        <!-- ─── ALERTS ─── -->
        <div v-for="a in alerts" :key="a.id"
          class="bg-frost text-white rounded-2xl px-4 py-3 flex items-center gap-3"
        >
          <div class="w-9 h-9 rounded-full bg-water/30 flex items-center justify-center shrink-0">
            <component :is="alertIcon[a.type] || AlertTriangle" :size="18" />
          </div>
          <div class="flex-1">
            <div class="text-[10px] font-bold uppercase tracking-wider opacity-75">Alerta climática</div>
            <div class="text-sm font-semibold">{{ ALERT_LABELS[a.type] }} · {{ formatAlertDate(a.date) }}</div>
          </div>
          <button @click="dismissAlert(a.id)" class="w-6 h-6 rounded-full bg-white/10 text-white/70 flex items-center justify-center text-sm">×</button>
        </div>

        <!-- ─── SATELLITE ─── -->
        <div v-if="rec.ndvi !== null || satelliteUrl" class="bg-surface border border-line rounded-3xl p-5">
          <div class="flex items-center justify-between mb-3">
            <div class="app-label">Imagen satelital · NDVI</div>
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-primary-soft text-primary text-[10px] font-bold uppercase tracking-wider">
              <Satellite :size="11" /> Sentinel-2 · {{ rec.ndvi_date }}
            </span>
          </div>
          <div v-if="satelliteUrl" ref="mapRef" class="w-full h-56 md:h-60 rounded-2xl overflow-hidden mb-3"></div>
          <div v-if="satelliteUrl" class="flex items-center gap-3 mb-3">
            <span class="app-label w-16">Opacidad</span>
            <input type="range" min="0" max="1" step="0.05" v-model.number="overlayOpacity"
                class="flex-1 accent-primary" />
            <span class="app-mono text-xs text-muted w-8 text-right">{{ Math.round(overlayOpacity * 100) }}%</span>
            </div>
          <div class="flex items-center gap-2 mb-3.5">
            <span class="app-label">Estrés</span>
            <div class="flex-1 h-1.5 rounded-full" style="background: linear-gradient(to right, #d73027, #fc8d59, #fee08b, #a6d96a, #1a9850)" />
            <span class="app-label">Vigor</span>
          </div>
          <div class="grid grid-cols-3 gap-3 md:gap-4">
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
              <div class="app-mono text-base font-bold mt-0.5" :class="{ 'text-amber': ndviAge > 15 }">
                {{ ndviAge }} d
              </div>
            </div>
          </div>
          <p v-if="ndviAge > 15" class="text-xs text-amber mt-3 leading-relaxed">
            La imagen tiene más de 15 días. El Kc puede no reflejar el estado actual del cultivo.
          </p>
        </div>
      </div>

      <!-- Right column: balance + cultivo + confirm CTA -->
      <div class="flex flex-col gap-3 md:gap-4">

        <!-- ─── BALANCE HÍDRICO ─── -->
        <div class="bg-surface border border-line rounded-3xl p-5">
          <div class="app-label mb-3">Balance hídrico</div>
          <SoilTank :deficit-pct="deficitPct" />
          <div class="grid grid-cols-2 gap-x-4 gap-y-3.5 mt-4 pt-4 border-t border-line">
            <div>
              <div class="app-label">Déficit actual</div>
              <div class="app-mono text-base font-bold mt-0.5">{{ rec.water_deficit_mm?.toFixed(1) }} <span class="text-sm text-muted font-semibold">mm</span></div>
            </div>
            <div>
              <div class="app-label">TAW</div>
              <div class="app-mono text-base font-bold mt-0.5">{{ rec.taw_mm?.toFixed(0) }} <span class="text-sm text-muted font-semibold">mm</span></div>
            </div>
            <div>
              <div class="app-label">RAW</div>
              <div class="app-mono text-base font-bold mt-0.5">{{ rec.raw_mm?.toFixed(0) }} <span class="text-sm text-muted font-semibold">mm</span></div>
            </div>
            <div>
              <div class="app-label">Estrés Ks</div>
              <div class="app-mono text-base font-bold mt-0.5">{{ rec.ks?.toFixed(2) }}</div>
            </div>
          </div>
        </div>

        <!-- ─── CULTIVO ─── -->
        <div class="bg-surface border border-line rounded-3xl p-5">
          <div class="app-label mb-3">Cultivo · Kc</div>
          <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
            <div>
              <div class="app-label">Etapa</div>
              <div class="text-sm font-bold mt-0.5">{{ STAGE_LABELS[rec.phenological_stage] }}</div>
            </div>
            <div>
              <div class="app-label">Kc</div>
              <div class="app-mono text-base font-bold mt-0.5">{{ rec.kc?.toFixed(3) }}</div>
            </div>
            <div>
              <div class="app-label">Fuente Kc</div>
              <div class="text-sm font-bold mt-0.5">{{ KC_SOURCE_LABELS[rec.kc_source] }}</div>
            </div>
            <div>
              <div class="app-label">ETo ayer</div>
              <div class="app-mono text-base font-bold mt-0.5">{{ rec.eto_mm?.toFixed(2) }} <span class="text-sm text-muted font-semibold">mm</span></div>
            </div>
          </div>
        </div>

        <!-- ─── CONFIRM CTA (desktop) ─── -->
        <div class="hidden md:block bg-primary-soft rounded-3xl p-5">
          <div class="flex items-center gap-3 mb-2.5">
            <div class="w-8 h-8 rounded-xl bg-primary text-primary-ink flex items-center justify-center">
              <Droplet :size="16" />
            </div>
            <div class="text-[11px] font-bold uppercase tracking-wider text-primary">Confirmá el riego</div>
          </div>
          <p class="text-sm text-ink leading-relaxed mb-3.5">
            Cuando hayas regado, confirmá cuántos mm aplicaste para que recalibremos el balance hídrico.
          </p>
          <RouterLink :to="`/fields/${route.params.id}/confirmations`"
            class="w-full bg-primary text-primary-ink font-bold text-sm py-3 rounded-xl flex items-center justify-center gap-1.5">
            Confirmar riego
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

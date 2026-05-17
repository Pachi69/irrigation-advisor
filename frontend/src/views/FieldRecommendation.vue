<script setup>
import  { ref, onMounted, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useRoute, useRouter} from 'vue-router'
import { getRecommendation, getFieldAlerts, getFieldSatelliteImage, getFieldById } from '../services/fields'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { ArrowLeft, Clock, AlertTriangle, Droplets, Leaf, Satellite } from 'lucide-vue-next'
import { ALERT_LABELS, URGENCY_LABELS, STAGE_LABELS, KC_SOURCE_LABELS, CONFIDENCE_LABELS } from '../utils/labels'

const router = useRouter()
const route = useRoute()

const rec = ref(null)
const loading = ref(true)
const error = ref('')

const alerts = ref([])
const dismissedAlerts = JSON.parse(localStorage.getItem('dismissedAlerts') || '[]')

const urgencyCardClass = computed(() => {
  const map = {
    low:      'bg-green-700',
    medium:   'bg-amber-500',
    high:     'bg-orange-600',
    critical: 'bg-red-600',
  }
  return map[rec.value?.urgency_level] ?? 'bg-green-700'
})

const urgencyBarClass = computed(() => {
  const map = {
    low:      'bg-green-400',
    medium:   'bg-amber-300',
    high:     'bg-orange-400',
    critical: 'bg-red-400',
  }
  return map[rec.value?.urgency_level] ?? 'bg-green-400'
})

const ndviAge = computed(() => {
    if (!rec.value?.ndvi_date) return null
    const days = Math.floor(
        (new Date() - new Date(rec.value.ndvi_date)) / (1000 * 60 * 60 * 24)
    )
    return days
})

const deficitPct = computed(() => {
    if (!rec.value) return 0
    return Math.min(100, Math.round((rec.value.water_deficit_mm / rec.value.taw_mm) * 100))
})

async function load() {
    try {
        rec.value = await getRecommendation(route.params.id)
    } catch (err) {
        error.value = err.response?.data?.detail || "No se pudo obtener la recomendacion"
    } finally {
        loading.value = false
    }
}

function formatAlertDate(dateStr) {
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(today.getDate() + 1)
    const d = new Date(dateStr + 'T00:00:00')
    if (d.toDateString() === tomorrow.toDateString()) return 'mañana'
    return d.toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
}

async function fetchAlerts() {
    try {
        const all = await getFieldAlerts(route.params.id)
        alerts.value = all.filter(a => !dismissedAlerts.includes(a.id))
    } catch {
        // Alertas opcionales
    }
}

function dismissAlert(id) {
    const updated = [...dismissedAlerts, id]
    localStorage.setItem('dismissedAlerts', JSON.stringify(updated))
    alerts.value = alerts.value.filter(a => a.id !== id)
}


const satelliteImageUrl = ref(null)
const mapRef = ref(null)
let map = null
const overlayOpacity = ref(0.8)
let overlayLayer = null

async function loadSatelliteImage() {
    try {
        const blob = await getFieldSatelliteImage(route.params.id)
        satelliteImageUrl.value = URL.createObjectURL(blob)
    } catch {
        // Imagen satelital opcional
    }
}

const fieldData = ref(null)

async function loadFieldData() {
    try {
        fieldData.value = await getFieldById(route.params.id)
    } catch {
    }
}

watch([satelliteImageUrl, fieldData, rec], ([imgUrl, field]) => {
    if (!imgUrl || !field?.polygon_geojson) return
    if (!mapRef.value || map) return

    const coords = field.polygon_geojson.coordinates[0]
    const lats = coords.map(c => c[1])
    const lngs = coords.map(c => c[0])
    const bounds = [
        [Math.min(...lats), Math.min(...lngs)],
        [Math.max(...lats), Math.max(...lngs)],
    ]

    map = L.map(mapRef.value, { zoomControl: true, attributionControl: false})

L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    }).addTo(map)
    overlayLayer = L.imageOverlay(imgUrl, bounds, { opacity: overlayOpacity.value }).addTo(map)
    L.polygon(coords.map(c => [c[1], c[0]]), {
        color: 'white', weight: 2, fill: false
    }).addTo(map)
    map.fitBounds(bounds, { padding: [10, 10]})
    setTimeout(() => map?.invalidateSize(), 100)
}, { flush: 'post' })

watch(overlayOpacity, (val) => { overlayLayer?.setOpacity(val) })

onBeforeUnmount(() => { map?.remove(); map = null; overlayLayer = null })

onMounted(() => { load(); fetchAlerts(); loadSatelliteImage(); loadFieldData() })
</script>

<template>
    <div class="max-w-2xl lg:max-w-3xl mx-auto px-4 py-6 space-y-4">

        <div class="flex items-center justify-between">
            <button
                @click="router.push('/fields')"
                class="flex items-center gap-1 text-green-800 font-semibold text-sm hover:underline"
            >
                <ArrowLeft class="w-4 h-4" />
                Mis campos
            </button>
            <span v-if="rec" class="text-xs text-gray-400">{{ rec.date }}</span>
            <RouterLink
                :to="`/fields/${route.params.id}/history`"
                class="flex items-center gap-1 text-sm font-semibold text-green-800 border-2 border-green-800 px-3 py-1.5 rounded-xl hover:bg-green-50 transition-colors"
            >
                <Clock class="w-3.5 h-3.5" />
                Historial
            </RouterLink>
        </div>

        <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">Calculando recomendación...</div>
        <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>

        <template v-else-if="rec">

            <!-- Tarjeta de urgencia -->
            <div :class="['rounded-2xl p-5 text-center shadow-sm', urgencyCardClass]">
                <p class="text-white text-xs font-bold uppercase tracking-widest opacity-80 mb-1">
                    {{ URGENCY_LABELS[rec.urgency_level] }}
                </p>
                <p class="text-white font-black mb-1" style="font-size: 3.5rem; line-height: 1.1">
                    {{ rec.recommended_irrigation_mm > 0 ? `${rec.recommended_irrigation_mm} mm` : '0 mm' }}
                </p>
                <p class="text-white font-bold text-base mb-2">
                    {{ rec.recommended_irrigation_mm > 0 ? 'Regar hoy' : 'No se requiere riego hoy' }}
                </p>
                <p class="text-white text-sm opacity-90 leading-snug mb-3">{{ rec.reason }}</p>
                <div class="inline-flex items-center gap-1.5 bg-black bg-opacity-20 rounded-full px-3 py-1">
                    <span class="text-white text-xs opacity-75">Confianza:</span>
                    <span class="text-white text-xs font-bold">{{ CONFIDENCE_LABELS[rec.confidence] }}</span>
                </div>
            </div>

            <!-- Alertas climáticas -->
            <div v-if="alerts.length > 0" class="space-y-2">
                <p class="text-xs font-bold uppercase tracking-wider text-gray-400 px-1">Alertas climáticas</p>
                <div
                    v-for="alert in alerts" :key="alert.id"
                    :class="[
                        'flex items-center justify-between px-4 py-3 rounded-2xl border-2',
                        alert.type === 'frost' ? 'bg-blue-50 border-blue-300' : 'bg-orange-50 border-orange-300'
                    ]"
                >
                    <div class="flex items-center gap-2">
                        <AlertTriangle :class="['w-4 h-4', alert.type === 'frost' ? 'text-blue-600' : 'text-orange-600']" />
                        <div>
                            <p :class="['text-sm font-bold', alert.type === 'frost' ? 'text-blue-900' : 'text-orange-900']">
                                {{ ALERT_LABELS[alert.type] }}
                            </p>
                            <p :class="['text-xs', alert.type === 'frost' ? 'text-blue-600' : 'text-orange-600']">
                                {{ formatAlertDate(alert.date) }}
                            </p>
                        </div>
                    </div>
                    <button @click="dismissAlert(alert.id)" class="text-gray-400 hover:text-gray-600 text-lg leading-none px-1">✕</button>
                </div>
            </div>

            <!-- Balance hídrico -->
            <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-4">
                <div class="flex items-center gap-2 mb-3">
                    <Droplets class="w-4 h-4 text-green-700" />
                    <p class="text-xs font-bold uppercase tracking-wider text-gray-400">Balance hídrico</p>
                </div>
                <div class="flex items-center gap-3 mb-4">
                    <div class="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                        <div :class="['h-full rounded-full transition-all', urgencyBarClass]" :style="{ width: deficitPct + '%' }" />
                    </div>
                    <span class="text-sm font-bold text-gray-700 w-12 text-right">{{ deficitPct }}%</span>
                </div>
                <div class="grid grid-cols-2 gap-x-4 gap-y-3">
                    <div>
                        <p class="text-xs text-gray-400">Déficit actual</p>
                        <p class="text-base font-bold text-gray-900">{{ rec.water_deficit_mm?.toFixed(1) }} mm</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">TAW <span class="font-normal">(agua total)</span></p>
                        <p class="text-base font-bold text-gray-900">{{ rec.taw_mm?.toFixed(1) }} mm</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">RAW <span class="font-normal">(límite sin estrés)</span></p>
                        <p class="text-base font-bold text-gray-900">{{ rec.raw_mm?.toFixed(1) }} mm</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">Estrés hídrico (Ks)</p>
                        <p class="text-base font-bold text-gray-900">{{ rec.ks?.toFixed(2) }}</p>
                    </div>
                </div>
            </div>

            <!-- Cultivo y Kc -->
            <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-4">
                <div class="flex items-center gap-2 mb-3">
                    <Leaf class="w-4 h-4 text-green-700" />
                    <p class="text-xs font-bold uppercase tracking-wider text-gray-400">Cultivo · Kc</p>
                </div>
                <div class="grid grid-cols-2 gap-x-4 gap-y-3">
                    <div>
                        <p class="text-xs text-gray-400">Etapa fenológica</p>
                        <p class="text-sm font-bold text-gray-900">{{ STAGE_LABELS[rec.phenological_stage] }}</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">Kc</p>
                        <p class="text-sm font-bold text-gray-900">{{ rec.kc?.toFixed(3) }}</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">Fuente Kc</p>
                        <p class="text-sm font-bold text-gray-900">{{ KC_SOURCE_LABELS[rec.kc_source] }}</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">ETo ayer</p>
                        <p class="text-sm font-bold text-gray-900">{{ rec.eto_mm?.toFixed(2) }} mm/día</p>
                    </div>
                </div>
            </div>

            <!-- Imagen satelital -->
            <div v-if="rec.ndvi !== null || satelliteImageUrl" class="bg-white rounded-2xl border border-gray-200 shadow-sm p-4">
                <div class="flex items-center gap-2 mb-3">
                    <Satellite class="w-4 h-4 text-green-700" />
                    <p class="text-xs font-bold uppercase tracking-wider text-gray-400">Imagen satelital</p>
                </div>

                <div v-if="satelliteImageUrl">
                    <div ref="mapRef" class="w-full h-56 rounded-xl overflow-hidden mb-3" />
                    <div class="flex items-center gap-2 mb-3">
                        <span class="text-xs text-gray-400">Estrés</span>
                        <div class="flex-1 h-2 rounded-full" style="background: linear-gradient(to right, #d73027, #fc8d59, #fee08b, #a6d96a, #1a9850)" />
                        <span class="text-xs text-gray-400">Vigor</span>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="text-xs text-gray-500 w-16">Opacidad</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="overlayOpacity" class="flex-1 accent-green-700" />
                        <span class="text-xs text-gray-500 w-8 text-right">{{ Math.round(overlayOpacity * 100) }}%</span>
                    </div>
                </div>

                <div v-if="rec.ndvi !== null" class="grid grid-cols-3 gap-3 mt-3">
                    <div>
                        <p class="text-xs text-gray-400">NDVI</p>
                        <p class="text-sm font-bold text-gray-900">{{ rec.ndvi?.toFixed(4) }}</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">Fecha imagen</p>
                        <p :class="['text-sm font-bold', ndviAge > 15 ? 'text-orange-600' : 'text-gray-900']">{{ rec.ndvi_date }}</p>
                    </div>
                    <div v-if="rec.cloud_cover_pct != null">
                        <p class="text-xs text-gray-400">Nubosidad</p>
                        <p class="text-sm font-bold text-gray-900">{{ rec.cloud_cover_pct?.toFixed(0) }}%</p>
                    </div>
                </div>

                <p v-if="ndviAge > 15" class="text-xs text-orange-600 mt-3">
                    La imagen tiene más de 15 días. El Kc puede no reflejar el estado actual del cultivo.
                </p>
                <p v-if="rec.ndvi === null && !satelliteImageUrl" class="text-xs text-gray-400">
                    No hay imagen reciente disponible. Se usó Kc tabular FAO-56.
                </p>
            </div>

        </template>
    </div>
</template>
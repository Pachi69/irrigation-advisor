<script setup>
/**
 * DemoView.vue — Sección DEMO (desacoplada del producto).
 * Corre el pipeline de recomendación sobre una fecha de verano preset, con NDVI
 * satelital activo, para mostrar que el sistema funciona en cualquier temporada.
 * No afecta los campos del usuario: usa un fixture en memoria en el backend.
 */
import { ref, computed, watch, onBeforeUnmount, useTemplateRef } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getDemoSnapshot, getDemoSatelliteImage } from '../services/demo.js'
import {
ArrowLeft, FlaskConical, Satellite, Play, Snowflake, Sun,
} from 'lucide-vue-next'
import {
STAGE_LABELS, KC_SOURCE_LABELS, CONFIDENCE_LABELS, CROP_LABELS,
} from '../utils/labels.js'
import UrgencyHero from '../components/UrgencyHero.vue'
import SoilTank from '../components/SoilTank.vue'
import Sparkline from '../components/Sparkline.vue'

const router = useRouter()

const snapshot = ref(null)
const loading = ref(false)
const error = ref('')

const satelliteUrl = ref(null)
const mapRef = useTemplateRef('mapRef')
let map = null
let overlayLayer = null
const overlayOpacity = ref(0.8)

const todayLabel = computed(() =>
    new Date().toLocaleDateString('es-AR', { day: 'numeric', month: 'long', year: 'numeric' })
)

const targetLabel = computed(() => {
    if (!snapshot.value?.target_date) return ''
    return new Date(snapshot.value.target_date + 'T00:00:00').toLocaleDateString('es-AR', { day: 'numeric', month: 'long', year: 'numeric' })
})

const deficitPct = computed(() => {
    if (!snapshot.value) return 0
    return Math.min(100, Math.round((snapshot.value.water_deficit_mm / snapshot.value.taw_mm) * 100))
})

const deficitTrace = computed(() =>
    (snapshot.value?.trajectory || []).map(p => p.deficit_pct)
)

async function run() {
    loading.value = true
    error.value = ''
    try {
        snapshot.value = await getDemoSnapshot()
        loadSatellite()
    } catch (e) {
        error.value = e?.response?.data?.detail || 'No se pudo calcular la demo'
    } finally {
        loading.value = false
    }
}

async function loadSatellite() {
    try {
        const blob = await getDemoSatelliteImage()
        satelliteUrl.value = URL.createObjectURL(blob)
    } catch {}
}

// Init Leaflet una vez que hay imagen + polígono
watch([satelliteUrl, snapshot], ([url, s]) => {
    if (!url || !s?.polygon_geojson || !mapRef.value || map) return
    const coords = s.polygon_geojson.coordinates[0]
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
</script>

<template>
    <div class="max-w-[1180px] mx-auto px-4 md:px-8 pt-2 md:pt-6 pb-8">

        <!-- Back -->
        <button @click="router.push('/')" class="flex items-center gap-1.5 text-primary font-semibold text-sm mb-4">
        <ArrowLeft :size="16" /> Volver al inicio
        </button>

        <!-- ─── Banner MODO DEMO ─── -->
        <div class="bg-amber-soft border border-amber/30 rounded-2xl p-4 flex items-start gap-3 mb-5">
            <div class="w-9 h-9 rounded-xl bg-amber text-white flex items-center justify-center shrink-0">
                <FlaskConical :size="18" />
            </div>
            <div class="flex-1">
                <div class="text-sm font-bold text-ink">Modo demo</div>
                <div class="text-xs text-muted leading-relaxed">
                    Corre el pipeline completo sobre datos reales de una fecha de verano (Sentinel-2 + clima),
                    para mostrar el sistema con NDVI satelital activo. No afecta tus campos.
                </div>
            </div>
        </div>

        <h1 class="text-2xl md:text-3xl font-bold text-ink tracking-tight leading-tight mb-1">
            Vid · Malbec en plena temporada
        </h1>
        <div class="text-sm text-muted mb-5">
            Mismo lote de prueba · 7.3 ha · imagen y clima del 3 de febrero de 2026
        </div>

        <!-- ─── Intro + botón (antes de correr) ─── -->
        <div v-if="!snapshot && !loading" class="bg-surface border border-line rounded-3xl p-6 md:p-8">
            <p class="text-sm text-ink leading-relaxed mb-2">
                <span class="font-bold">Hoy ({{ todayLabel }})</span> el lote está en <span class="font-bold">reposo invernal</span>:
                el sistema usa un <span class="font-bold">Kc tabular (0.20)</span> y el NDVI no se utiliza.
            </p>
            <p class="text-sm text-muted leading-relaxed mb-6">
                Al correr la demo, el sistema se ubica en una fecha de verano, trae la imagen Sentinel-2
                de esa fecha y deriva el <span class="font-semibold">Kc dinámico desde el NDVI</span>,
                calcula ETo, lleva el balance hídrico y da la recomendación que corresponda.
            </p>
            <button @click="run"
                class="inline-flex items-center gap-2 bg-primary text-primary-ink font-bold text-sm px-5 py-3 rounded-xl">
                <Play :size="16" /> Correr el pipeline · 3 feb 2026
            </button>
            <p class="text-xs text-muted mt-3">La primera vez puede tardar unos segundos (consulta GEE + Open-Meteo).</p>
        </div>

        <div v-if="loading" class="text-center py-12 text-muted text-sm">
            Consultando Sentinel-2 y clima…
        </div>
        <div v-if="error" class="bg-rust-soft border border-rust/20 text-rust text-sm font-medium px-4 py-3 rounded-2xl">
            {{ error }}
        </div>

        <!-- ─── Resultados ─── -->
        <div v-if="snapshot" class="flex flex-col gap-3 md:gap-4">

            <!-- Contraste reposo vs verano (la estrella) -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                <div class="bg-chip border border-line rounded-3xl p-5">
                    <div class="flex items-center gap-2 mb-3">
                        <Snowflake :size="16" class="text-muted" />
                        <div class="app-label">Hoy · reposo invernal</div>
                    </div>
                    <div class="app-mono text-3xl font-bold text-muted">{{ snapshot.current_kc?.toFixed(2) }}</div>
                    <div class="text-xs text-muted mt-1">
                        Kc {{ KC_SOURCE_LABELS[snapshot.current_kc_source] }} · {{ STAGE_LABELS[snapshot.current_phenological_stage] }}
                    </div>
                    <div class="text-xs text-muted mt-2 leading-relaxed">El NDVI satelital no se usa en reposo.</div>
                </div>
                <div class="bg-primary-soft rounded-3xl p-5">
                    <div class="flex items-center gap-2 mb-3">
                        <Sun :size="16" class="text-primary" />
                        <div class="app-label text-primary/80">{{ targetLabel }} · plena temporada</div>
                    </div>
                    <div class="app-mono text-3xl font-bold text-primary">{{ snapshot.kc?.toFixed(3) }}</div>
                    <div class="text-xs text-primary/80 mt-1">
                        Kc {{ KC_SOURCE_LABELS[snapshot.kc_source] }} · {{ STAGE_LABELS[snapshot.phenological_stage] }}
                    </div>
                    <div class="text-xs text-primary/80 mt-2 leading-relaxed">
                        Derivado del NDVI satelital ({{ snapshot.ndvi?.toFixed(3) }}) de esa fecha.
                    </div>
                </div>
            </div>

            <!-- Grid principal -->
            <div class="grid md:grid-cols-[1.3fr_1fr] gap-3 md:gap-4">

                <!-- Izquierda: hero + satélite + trayectoria -->
                <div class="flex flex-col gap-3 md:gap-4">
                    <UrgencyHero
                        :mm="snapshot.recommended_irrigation_mm"
                        :time-min="snapshot.time_min"
                        :volume-m3="snapshot.volume_m3"
                        :urgency="snapshot.urgency_level"
                        :reason="snapshot.reason"
                        :date-label="`${targetLabel}`"
                        :confidence="CONFIDENCE_LABELS[snapshot.confidence] || 'Sin datos'"
                    />

                    <!-- Satélite -->
                    <div class="bg-surface border border-line rounded-3xl p-5">
                        <div class="flex items-center justify-between mb-3">
                            <div class="app-label">Imagen satelital · NDVI</div>
                            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-primary-soft text-primary text-[10px] font-bold uppercase tracking-wider">
                                <Satellite :size="11" /> Sentinel-2 · {{ snapshot.ndvi_date }}
                            </span>
                        </div>
                        <div v-if="satelliteUrl" ref="mapRef" class="w-full h-56 md:h-60 rounded-2xl overflow-hidden mb-3"></div>
                        <div v-if="satelliteUrl" class="flex items-center gap-3 mb-3">
                            <span class="app-label w-16">Opacidad</span>
                            <input type="range" min="0" max="1" step="0.05" v-model.number="overlayOpacity" class="flex-1 accent-primary" />
                            <span class="app-mono text-xs text-muted w-8 text-right">{{ Math.round(overlayOpacity * 100) }}%</span>
                        </div>
                        <div class="flex items-center gap-2 mb-3.5">
                            <span class="app-label">Estrés</span>
                            <div class="flex-1 h-1.5 rounded-full" style="background: linear-gradient(to right, #d73027, #fc8d59, #fee08b, #a6d96a, #1a9850)" />
                            <span class="app-label">Vigor</span>
                        </div>
                        <div class="grid grid-cols-3 gap-3">
                            <div>
                                <div class="app-label">NDVI</div>
                                <div class="app-mono text-base font-bold mt-0.5">{{ snapshot.ndvi?.toFixed(3) }}</div>
                            </div>
                            <div>
                                <div class="app-label">Nubosidad</div>
                                <div class="app-mono text-base font-bold mt-0.5">{{ snapshot.cloud_cover_pct?.toFixed(0) }}%</div>
                            </div>
                            <div>
                                <div class="app-label">ETc día</div>
                                <div class="app-mono text-base font-bold mt-0.5">{{ snapshot.etc_mm?.toFixed(2) }} <span class="text-sm text-muted font-semibold">mm</span></div>
                            </div>
                        </div>
                    </div>

                    <!-- Trayectoria del déficit -->
                    <div class="bg-surface border border-line rounded-3xl p-5">
                        <div class="app-label mb-1">Trayectoria del déficit (% TAW)</div>
                        <div class="text-xs text-muted mb-3">
                            Desde la lluvia ancla ({{ snapshot.anchor_date }}) hasta el {{ snapshot.target_date }}
                        </div>
                        <Sparkline v-if="deficitTrace.length > 1" :data="deficitTrace" color="var(--color-amber)" :width="640" :height="60" class="w-full" />
                    </div>
                </div>

                <!-- Derecha: balance + cultivo -->
                <div class="flex flex-col gap-3 md:gap-4">
                    <div class="bg-surface border border-line rounded-3xl p-5">
                        <div class="app-label mb-3">Balance hídrico</div>
                        <SoilTank :deficit-pct="deficitPct" />
                        <div class="grid grid-cols-2 gap-x-4 gap-y-3.5 mt-4 pt-4 border-t border-line">
                            <div>
                                <div class="app-label">Déficit <span class="normal-case font-normal tracking-normal">(Dr)</span></div>
                                <div class="app-mono text-base font-bold mt-0.5">{{ snapshot.water_deficit_mm?.toFixed(1) }} <span class="text-sm text-muted font-semibold">mm</span></div>
                            </div>
                            <div>
                                <div class="app-label">TAW</div>
                                <div class="app-mono text-base font-bold mt-0.5">{{ snapshot.taw_mm?.toFixed(0) }} <span class="text-sm text-muted font-semibold">mm</span></div>
                            </div>
                            <div>
                                <div class="app-label">RAW <span class="normal-case font-normal tracking-normal">(umbral)</span></div>
                                <div class="app-mono text-base font-bold mt-0.5">{{ snapshot.raw_mm?.toFixed(0) }} <span class="text-sm text-muted font-semibold">mm</span></div>
                            </div>
                            <div>
                                <div class="app-label">Estrés <span class="normal-case font-normal tracking-normal">(Ks)</span></div>
                                <div class="app-mono text-base font-bold mt-0.5">{{ snapshot.ks?.toFixed(2) }}</div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-surface border border-line rounded-3xl p-5">
                        <div class="app-label mb-3">Cultivo · Kc</div>
                        <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
                            <div>
                                <div class="app-label">Etapa</div>
                                <div class="text-sm font-bold mt-0.5">{{ STAGE_LABELS[snapshot.phenological_stage] }}</div>
                            </div>
                            <div>
                                <div class="app-label">Kc</div>
                                <div class="app-mono text-base font-bold mt-0.5">{{ snapshot.kc?.toFixed(3) }}</div>
                            </div>
                            <div>
                                <div class="app-label">Fuente Kc</div>
                                <div class="text-sm font-bold mt-0.5">{{ KC_SOURCE_LABELS[snapshot.kc_source] }}</div>
                            </div>
                            <div>
                                <div class="app-label">ETo</div>
                                <div class="app-mono text-base font-bold mt-0.5">{{ snapshot.eto_mm?.toFixed(2) }} <span
                class="text-sm text-muted font-semibold">mm</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Nota de transparencia -->
            <p class="text-xs text-muted leading-relaxed px-1">{{ snapshot.note }}</p>
        </div>
    </div>
</template>
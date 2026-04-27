<script setup>
import  { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter} from 'vue-router'
import { getRecommendation, getFieldAlerts } from '../services/fields'

const router = useRouter()
const route = useRoute()

const rec = ref(null)
const loading = ref(true)
const error = ref('')

const alerts = ref([])
const dismissedAlerts = JSON.parse(localStorage.getItem('dismissedAlerts') || '[]')

const ALERT_LABELS = {
    frost: 'Alerta de helada',
    heat_wave: 'Alerta de ola de calor',
}

const URGENCY_LABELS = {
    low: 'Sin urgencia',
    medium: 'Urgencia moderada',
    high: 'Urgencia alta',
    critical: 'CRÍTICO — Riegue hoy',
}

const STAGE_LABELS = {
    initial: 'Etapa inicial',
    development: 'Desarrollo',
    mid: 'Etapa media',
    late: 'Etapa tardía',
}

const KC_SOURCE_LABELS = {
    s2_dynamic: 'Satelital (Sentinel-2)',
    tabular: 'Tabular (FAO-56)',
}

const CONFIDENCE_LABELS = {
    high: 'Alta',
    medium: 'Media',
    low: 'Baja',
}

const urgencyClass = computed(() => `urgency-${rec.value.urgency_level}`)

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

onMounted(() => { load(); fetchAlerts() })
</script>

<template>
    <div class="rec-page">
        <header class="rec-header">
            <button class="btn-back" @click="router.push('/fields')"><- Mis campos</button>
            <span class="rec-date" v-if="rec">{{ rec.date }}</span>
        </header>

        <div v-if="loading" class="center">Calculando recomendacion...</div>
        <div v-else-if="error" class="error">{{ error }}</div>

        <template v-else-if="rec">
            <!-- Tarjeta principal de urgencia -->
             <div :class="['urgency-card', urgencyClass]">
                <div class="urgency-label">{{ URGENCY_LABELS[rec.urgency_level] }}</div>
                <div class="irrigation-mm" v-if="rec.recommended_irrigation_mm > 0">
                    Regar <strong>{{ rec.recommended_irrigation_mm }} mm</strong>
                </div>
                <div class="irrigation-mm" v-else>
                    No se requiere riego hoy
                </div>
                <p class="reason">{{ rec.reason }}</p>
                <span class="confidence">
                    Confianza: {{ CONFIDENCE_LABELS[rec.confidence] }}
                </span>
             </div>

             <!-- Alertas climaticas -->
              <section v-if="alerts.length > 0" class="section alerts-section">
                <h2>Alertas climaticas</h2>
                <div v-for="alert in alerts" :key="alert.id" :class="['alert-item', `alert-${alert.type}`]">
                    <span class="alert-icon">{{ ALERT_LABELS[alert.type] }}</span>
                    <span class="alert-date">{{ formatAlertDate(alert.date) }}</span>
                    <button class="alert-dismiss" @click="dismissAlert(alert.id)">X</button>
                </div>
              </section>

             <!-- Balance hidrico-->
              <section class="section">
                <h2>Balance hidrico</h2>
                <div class="deficit-bar-wrap">
                    <div class="deficit-bar">
                        <div class="deficit-fill" :style="{ width: deficitPct + '%'}"
                            :class="urgencyClass"></div>
                    </div>
                    <span class="deficit-pct">{{ deficitPct }}% del TAW</span>
                </div>
                <dl class="data-grid">
                    <div>
                        <dt>Deficit actual</dt>
                        <dd>{{ rec.water_deficit_mm?.toFixed(1) }} mm</dd>
                    </div>
                    <div>
                        <dt>TAW</dt>
                        <dd>{{ rec.taw_mm?.toFixed(1) }} mm</dd>
                    </div>
                    <div>
                        <dt>RAW</dt>
                        <dd>{{ rec.raw_mm?.toFixed(1) }} mm</dd>
                    </div>
                    <div>
                        <dt>Estres hidrico (Ks)</dt>
                        <dd>{{ rec.ks?.toFixed(2) }}</dd>
                    </div>
                </dl>
              </section>

              <!-- Cultivo y Kc -->
               <section class="section">
                <h2>Cultivo</h2>
                <dl class="data-grid">
                    <div>
                        <dt>Etapa fenológica</dt>
                        <dd>{{ STAGE_LABELS[rec.phenological_stage] }}</dd>
                    </div>
                    <div>
                        <dt>Kc</dt>
                        <dd>{{ rec.kc?.toFixed(3) }}</dd>
                    </div>
                    <div>
                        <dt>Fuente Kc</dt>
                        <dd>{{ KC_SOURCE_LABELS[rec.kc_source] }}</dd>
                    </div>
                    <div>
                        <dt>ETo ayer</dt>
                        <dd>{{ rec.eto_mm?.toFixed(2) }} mm/día</dd>
                    </div>
                </dl>
               </section>

               <!-- NDVI -->
                <section class="section" v-if="rec.ndvi !== null">
                    <h2>Imagen satelital</h2>
                    <dl class="data-grid">
                        <div>
                            <dt>NDVI</dt>
                            <dd>{{ rec.ndvi?.toFixed(4) }}</dd>
                        </div>
                        <div>
                            <dt>Fecha imagen</dt>
                            <dd :class="{ 'text-warning': ndviAge > 15 }">
                                {{ rec.ndvi_date }}
                                <span v-if="ndviAge !== null">(hace {{ ndviAge }} días)</span>
                            </dd>
                        </div>
                    </dl>
                    <p v-if="ndviAge > 15" class="warning-text">
                        La imagen tiene mas de 15 dias. El Kc puede no reflejar el estado actual del cultivo
                    </p>
                </section>
                <section class="section" v-else>
                    <h2>Imagen satelital</h2>
                    <p class="muted">No hay imagen reciente disponible. Se usó Kc tabular FAO-56.</p>
                </section>
        </template>
    </div>
</template>


<style scoped>
.rec-page {
    max-width: 600px;
    margin: 0 auto;
    padding: 1rem;
    font-family: sans-serif;
}

.rec-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.btn-back {
    background: none;
    border: none;
    color: #2e7d32;
    font-size: 1rem;
    cursor: pointer;
    padding: 0;
}

.rec-date {
    font-size: 0.9rem;
    color: #666;
}

/* Tarjeta de urgencia */
.urgency-card {
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
}

.urgency-low    { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.urgency-medium { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
.urgency-high   { background: #ffe0b2; color: #e65100; border: 1px solid #ffcc80; }
.urgency-critical { background: #ffcdd2; color: #c62828; border: 1px solid #ef9a9a; }

.urgency-label {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.irrigation-mm {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0.5rem 0;
}

.reason {
    font-size: 0.95rem;
    margin: 0.75rem 0 0.5rem;
    line-height: 1.4;
}

.confidence {
    font-size: 0.8rem;
    opacity: 0.8;
}

/* Secciones */
.section {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.section h2 {
    font-size: 1rem;
    color: #444;
    margin: 0 0 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Barra de déficit */
.deficit-bar-wrap {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}

.deficit-bar {
    flex: 1;
    height: 10px;
    background: #eee;
    border-radius: 5px;
    overflow: hidden;
}

.deficit-fill {
    height: 100%;
    border-radius: 5px;
    transition: width 0.4s;
}

.urgency-low    .deficit-fill,
.deficit-fill.urgency-low    { background: #2e7d32; }
.deficit-fill.urgency-medium { background: #f9a825; }
.deficit-fill.urgency-high   { background: #e65100; }
.deficit-fill.urgency-critical { background: #c62828; }

.deficit-pct {
    font-size: 0.85rem;
    color: #555;
    white-space: nowrap;
}

/* Grilla de datos */
.data-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin: 0;
}

.data-grid > div { display: flex; flex-direction: column; }
.data-grid dt { font-size: 0.78rem; color: #888; }
.data-grid dd { margin: 0; font-weight: 600; font-size: 0.95rem; }

/* Utilidades */
.center { text-align: center; padding: 2rem; color: #666; }
.error  { color: #c00; padding: 1rem; text-align: center; }
.muted  { color: #888; font-size: 0.9rem; margin: 0; }
.text-warning { color: #e65100; }
.warning-text {
    font-size: 0.85rem;
    color: #e65100;
    margin-top: 0.5rem;
    margin-bottom: 0;
}
.alerts-section h2 { color: #b71c1c; }
.alert-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0.75rem;
    border-radius: 6px;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
}
.alert-frost     { background: #e3f2fd; color: #0d47a1; }
.alert-heat_wave { background: #fff3e0; color: #e65100; }
.alert-date { font-size: 0.85rem; opacity: 0.8; }
.alert-dismiss {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.85rem;
    opacity: 0.5;
    padding: 0 0.25rem;
    line-height: 1;
}
.alert-dismiss:hover { opacity: 1; }
</style>
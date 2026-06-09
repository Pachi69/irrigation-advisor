<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSectorMetrics, getSectorById } from '../services/sectors'
import { ArrowLeft, Droplets, AlertTriangle, Satellite, CheckCircle2 } from 'lucide-vue-next'
import { URGENCY_LABEL, CROP_LABELS } from '../utils/labels'

const route = useRoute()
const router = useRouter()

const RANGES = [30, 60, 90]
const days = ref(90)

const data = ref(null)
const sector = ref(null)
const loading = ref(true)
const error = ref('')

const URG = {
    low:      { fg: 'var(--color-primary)',   dot: 'var(--color-primary)' },
    medium:   { fg: 'var(--color-amber-ink)', dot: 'var(--color-amber)' },
    high:     { fg: '#8A3D12',                dot: '#D8651C' },
    critical: { fg: 'var(--color-rust)',      dot: 'var(--color-rust)' },
}

const n0 = (v) => (v == null ? '—' : Math.round(v).toLocaleString('es-AR'))
const n1 = (v) => (v == null ? '—' : v.toFixed(1))
const n2 = (v) => (v == null ? '—' : v.toFixed(2))
const pct = (v) => (v == null ? '—' : `${v.toFixed(1)}%`)

function fmtWeek(ws) {
    return new Date(ws + 'T00:00:00').toLocaleDateString('es-AR', { day: '2-digit', month: 'short' })
}

const urgencyBar = computed(() => {
    if (!data.value) return []
    const u = data.value.urgency
    const total = u.low + u.medium + u.high + u.critical || 1
    return ['low', 'medium', 'high', 'critical']
        .map((key) => ({ key, n: u[key] }))
        .filter((x) => x.n > 0)
        .map((x) => ({ ...x, w: (x.n / total) * 100 }))
})

async function load() {
    loading.value = true
    error.value = ''
    try {
        data.value = await getSectorMetrics(route.params.id, { days: days.value })
    } catch {
        error.value = 'No se pudieron cargar las métricas'
    } finally {
        loading.value = false
    }
}

function setRange(d) {
    if (d === days.value) return
    days.value = d
    load()
}

onMounted(async () => {
    try { sector.value = await getSectorById(route.params.id) } catch {}
    await load()
})
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

            <!-- HERO: agua evitada -->
            <div class="bg-primary text-primary-ink rounded-3xl p-5 md:p-6">
                <div class="text-[11px] font-bold uppercase tracking-wider opacity-80">Agua evitada vs riego a ciegas</div>
                <div class="flex items-end gap-3 mt-1.5">
                    <span class="app-display text-5xl">{{ pct(data.water.avoided_pct) }}</span>
                    <div class="mb-1 leading-tight">
                          <div class="app-mono text-base font-semibold opacity-90">{{ n1(data.water.avoided_mm) }} mm</div>
                          <div class="app-mono text-sm opacity-70">{{ n0(data.water.avoided_m3) }} m³</div>
                      </div>
                </div>
                <p class="text-sm opacity-85 mt-2 leading-relaxed">
                    Aprovechando la lluvia y la reserva del suelo, el sistema evitó regar
                    {{ n1(data.water.avoided_mm) }} mm respecto de reponer la ETc a ciegas
                    ({{ n1(data.water.baseline_etc_mm) }} mm).
                </p>
            </div>

            <div class="grid md:grid-cols-2 gap-3 md:gap-4">

                <!-- AGUA -->
                <div class="bg-surface border border-line rounded-3xl p-5">
                    <div class="app-label mb-3 flex items-center gap-1.5"><Droplets :size="13" /> Agua del período</div>
                    <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
                        <div>
                            <div class="app-label">Necesaria (IRn)</div>
                            <div class="app-mono text-base font-bold mt-0.5">{{ n1(data.water.net_requirement_mm) }} <span class="text-sm text-muted font-semibold">mm</span></div>
                            <div class="app-mono text-xs text-muted">{{ n0(data.water.net_requirement_m3) }} m³</div>
                        </div>
                        <div>
                            <div class="app-label">Aplicada</div>
                            <div class="app-mono text-base font-bold mt-0.5">{{ n1(data.water.applied_mm) }} <span class="text-sm text-muted font-semibold">mm</span></div>
                            <div class="app-mono text-xs text-muted">{{ n0(data.water.applied_m3) }} m³</div>
                        </div>
                        <div>
                            <div class="app-label">Reposición ciega (ETc)</div>
                            <div class="app-mono text-base font-bold mt-0.5">{{ n1(data.water.baseline_etc_mm) }} <span class="text-sm text-muted font-semibold">mm</span></div>
                        </div>
                        <div>
                            <div class="app-label">Evitada</div>
                            <div class="app-mono text-base font-bold mt-0.5 text-primary">{{ n1(data.water.avoided_mm) }} <span class="text-sm text-muted font-semibold">mm</span></div>
                        </div>
                    </div>
                </div>

                <!-- ESTRÉS -->
                <div class="bg-surface border border-line rounded-3xl p-5">
                    <div class="app-label mb-3 flex items-center gap-1.5"><AlertTriangle :size="13" /> Estrés hídrico</div>
                    <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
                        <div>
                            <div class="app-label">Días en estrés (Ks&lt;1)</div>
                            <div class="app-mono text-base font-bold mt-0.5">{{ data.stress.stress_days }}<span class="text-sm text-muted font-semibold">/{{ data.stress.days_evaluated }}</span></div>
                            <div class="app-mono text-xs text-muted">{{ pct(data.stress.stress_days_pct) }}</div>
                        </div>
                        <div>
                            <div class="app-label">Severo (Ks&lt;0.5)</div>
                            <div class="app-mono text-base font-bold mt-0.5">{{ data.stress.severe_stress_days }} <span class="text-sm text-muted font-semibold">d</span></div>
                        </div>
                        <div>
                            <div class="app-label">Ks promedio</div>
                            <div class="app-mono text-base font-bold mt-0.5">{{ n2(data.stress.avg_ks) }}</div>
                            <div class="app-mono text-xs text-muted">mín {{ n2(data.stress.min_ks) }}</div>
                        </div>
                        <div>
                            <div class="app-label">Déficit prom</div>
                            <div class="app-mono text-base font-bold mt-0.5">{{ n1(data.stress.avg_deficit_mm) }} <span class="text-sm text-muted font-semibold">mm</span></div>
                            <div class="app-mono text-xs text-muted">{{ pct(data.stress.avg_deficit_pct) }} TAW</div>
                        </div>
                    </div>
                </div>

                <!-- ADHERENCIA -->
                <div class="bg-surface border border-line rounded-3xl p-5">
                    <div class="app-label mb-3 flex items-center gap-1.5"><CheckCircle2 :size="13" /> Adherencia</div>
                    <div class="app-display text-4xl text-ink">{{ pct(data.adherence.adherence_pct) }}</div>
                    <p class="text-sm text-muted mt-1.5 leading-relaxed">
                        {{ data.adherence.confirmed }} de {{ data.adherence.actionable }} riegos recomendados
                        confirmados · {{ data.adherence.pending }} pendientes.
                    </p>
                </div>

                <!-- SATÉLITE -->
                <div class="bg-surface border border-line rounded-3xl p-5">
                    <div class="app-label mb-3 flex items-center gap-1.5"><Satellite :size="13" /> Cobertura satelital</div>
                    <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
                        <div>
                            <div class="app-label">Días con Kc satelital</div>
                            <div class="app-mono text-base font-bold mt-0.5">{{ data.satellite.s2_dynamic_days }}<span class="text-sm text-muted font-semibold">/{{ data.satellite.days_evaluated }}</span></div>
                            <div class="app-mono text-xs text-muted">{{ pct(data.satellite.s2_dynamic_pct) }}</div>
                        </div>
                        <div>
                            <div class="app-label">NDVI prom</div>
                            <div class="app-mono text-base font-bold mt-0.5">{{ n2(data.satellite.avg_ndvi) }}</div>
                            <div class="app-mono text-xs text-muted">{{ data.satellite.ndvi_days }} días c/imagen</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- URGENCIA -->
            <div class="bg-surface border border-line rounded-3xl p-5">
                <div class="app-label mb-3">Distribución de urgencia</div>
                <div class="flex h-3 rounded-full overflow-hidden bg-chip">
                    <div v-for="seg in urgencyBar" :key="seg.key" :style="{ width: seg.w + '%', background: URG[seg.key].dot }"></div>
                </div>
                <div class="flex flex-wrap gap-x-4 gap-y-1.5 mt-3">
                    <div v-for="seg in urgencyBar" :key="seg.key" class="flex items-center gap-1.5 text-xs">
                        <span class="w-2 h-2 rounded-full" :style="{ background: URG[seg.key].dot }"></span>
                        <span class="text-muted">{{ URGENCY_LABEL[seg.key] }}</span>
                        <span class="app-mono font-bold text-ink">{{ seg.n }}</span>
                    </div>
                </div>
            </div>

            <!-- CLIMA -->
            <div class="bg-surface border border-line rounded-3xl p-5">
                <div class="app-label mb-3">Clima del período</div>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3.5">
                    <div><div class="app-label">ETo</div><div class="app-mono text-base font-bold mt-0.5">{{ n1(data.climate.eto_mm) }} <span class="text-sm text-muted font-semibold">mm</span></div></div>
                    <div><div class="app-label">ETc</div><div class="app-mono text-base font-bold mt-0.5">{{ n1(data.climate.etc_mm) }} <span class="text-sm text-muted font-semibold">mm</span></div></div>
                    <div><div class="app-label">Lluvia</div><div class="app-mono text-base font-bold mt-0.5">{{ n1(data.climate.rain_mm) }} <span class="text-sm text-muted font-semibold">mm</span></div></div>
                    <div><div class="app-label">Lluvia efectiva</div><div class="app-mono text-base font-bold mt-0.5">{{ n1(data.climate.effective_rain_mm) }} <span class="text-sm text-muted font-semibold">mm</span></div></div>
                </div>
            </div>

            <!-- SEMANAL -->
            <div class="bg-surface border border-line rounded-3xl p-5">
                <div class="app-label mb-3">Detalle semanal</div>

                <!-- desktop -->
                <div class="hidden md:block overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr>
                                <th class="app-label pb-2 text-left">Semana</th>
                                <th class="app-label pb-2 text-right">ETc</th>
                                <th class="app-label pb-2 text-right">Lluvia ef.</th>
                                <th class="app-label pb-2 text-right">Necesaria</th>
                                <th class="app-label pb-2 text-right">Aplicada</th>
                                <th class="app-label pb-2 text-right">Evitada</th>
                                <th class="app-label pb-2 text-right">Ks</th>
                                <th class="app-label pb-2 text-right">Estrés</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="w in data.weekly" :key="w.week_start" class="border-t border-line">
                                <td class="py-2 text-muted">{{ fmtWeek(w.week_start) }}</td>
                                <td class="py-2 text-right app-mono">{{ n1(w.etc_mm) }}</td>
                                <td class="py-2 text-right app-mono text-water">{{ n1(w.effective_rain_mm) }}</td>
                                <td class="py-2 text-right app-mono font-bold">{{ n1(w.net_requirement_mm) }}</td>
                                <td class="py-2 text-right app-mono">{{ n1(w.applied_mm) }}</td>
                                <td class="py-2 text-right app-mono text-primary">{{ n1(w.avoided_mm) }}</td>
                                <td class="py-2 text-right app-mono">{{ n2(w.avg_ks) }}</td>
                                <td class="py-2 text-right app-mono">{{ w.stress_days }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- mobile -->
                <div class="md:hidden flex flex-col gap-2.5">
                    <div v-for="w in data.weekly" :key="w.week_start" class="border border-line rounded-2xl px-3.5 py-3">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm font-bold text-ink">{{ fmtWeek(w.week_start) }}</span>
                            <span class="app-mono text-xs text-muted">Ks {{ n2(w.avg_ks) }} · {{ w.stress_days }}d estrés</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2 text-center">
                            <div><div class="app-label">Necesaria</div><div class="app-mono text-sm font-bold">{{ n1(w.net_requirement_mm) }}</div></div>
                            <div><div class="app-label">Aplicada</div><div class="app-mono text-sm font-bold">{{ n1(w.applied_mm) }}</div></div>
                            <div><div class="app-label">Evitada</div><div class="app-mono text-sm font-bold text-primary">{{ n1(w.avoided_mm) }}</div></div>
                        </div>
                    </div>
                </div>

                <p class="text-[11px] text-soft mt-3 leading-relaxed">
                    La suma de “Necesaria” semanal puede superar el total del período: a nivel período la
                    lluvia se aprovecha a través de la reserva del suelo entre semanas.
                </p>
            </div>
        </div>
    </div>
</template>
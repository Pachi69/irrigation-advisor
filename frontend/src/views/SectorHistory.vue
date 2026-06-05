<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { getRecommendationHistory } from '../services/sectors'
import { ArrowLeft, BarChart2 } from 'lucide-vue-next'
import { URGENCY_LABEL } from '../utils/labels'

const route = useRoute()
const router = useRouter()

const history = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
    try {
        history.value = await getRecommendationHistory(route.params.id)
    } catch {
        error.value = 'No se pudo cargar el historial'
    } finally {
        loading.value = false
    }
})

const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

function dayOf(d) {
    const dt = new Date(d + 'T00:00:00')
    return isNaN(dt) ? String(d || '').slice(-2) : String(dt.getDate()).padStart(2, '0')
}
function monOf(d) {
    const dt = new Date(d + 'T00:00:00')
    return isNaN(dt) ? '' : MONTHS[dt.getMonth()].toUpperCase()
}
function deficitPct(item) {
    if (!item.taw_mm) return 0
    return Math.min(100, Math.max(0, Math.round((item.water_deficit_mm / item.taw_mm) * 100)))
}
function deficitColor(pct) {
    if (pct >= 75) return 'var(--color-rust)'
    if (pct >= 50) return '#D8651C'
    if (pct >= 30) return 'var(--color-amber)'
    return 'var(--color-water)'
}

const URG = {
    none:     { bg: 'var(--color-primary-soft)', fg: 'var(--color-primary)',   dot: 'var(--color-primary)', accent: 'var(--color-primary)' },
    low:      { bg: 'var(--color-primary-soft)', fg: 'var(--color-primary)',   dot: 'var(--color-primary)', accent: 'var(--color-primary)' },
    medium:   { bg: 'var(--color-amber-soft)',   fg: 'var(--color-amber-ink)', dot: 'var(--color-amber)',   accent: 'var(--color-amber)' },
    high:     { bg: '#F1D8C4',                    fg: '#8A3D12',                dot: '#D8651C',              accent: '#D8651C' },
    critical: { bg: 'var(--color-rust-soft)',    fg: 'var(--color-rust)',      dot: 'var(--color-rust)',    accent: 'var(--color-rust)' },
}
const urg = (u) => URG[u] || URG.none
</script>

<template>
    <div class="max-w-2xl lg:max-w-3xl mx-auto px-4 py-6">

        <div class="flex items-center justify-between mb-5">
            <button
                @click="router.push(`/sectors/${route.params.id}/recommendation`)"
                class="flex items-center gap-1 text-primary font-semibold text-sm hover:underline"
            >
                <ArrowLeft class="w-4 h-4" />
                Recomendación
            </button>
            <h1 class="text-base font-bold text-ink">Historial</h1>
            <RouterLink
                :to="`/sectors/${route.params.id}/chart`"
                class="flex items-center gap-1 text-sm font-semibold text-primary border-2 border-primary px-3 py-1.5 rounded-xl hover:bg-primary-soft transition-colors"
            >
                <BarChart2 class="w-3.5 h-3.5" />
                Gráfico
            </RouterLink>
        </div>

        <div v-if="loading" class="text-center py-12 text-soft text-sm">Cargando historial...</div>
        <div v-else-if="error" class="bg-rust-soft border border-rust/30 text-rust text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>
        <div v-else-if="history.length === 0" class="text-center py-12 text-soft text-sm">Sin historial disponible.</div>

        <template v-else>
            <!-- MOBILE -->
            <div class="md:hidden flex flex-col gap-2.5">
                <div
                    v-for="item in history"
                    :key="item.id"
                    class="bg-surface rounded-2xl border border-line px-4 py-3.5"
                    :style="{ borderLeft: `4px solid ${urg(item.urgency).accent}` }"
                >
                    <!-- nivel 1: fecha · resultado -->
                    <div class="flex items-baseline justify-between mb-3">
                        <div class="flex items-baseline gap-1.5">
                            <span class="app-mono text-2xl font-bold text-ink tracking-tight">{{ dayOf(item.date) }}</span>
                            <span class="app-label">{{ monOf(item.date) }}</span>
                        </div>
                        <div class="text-right">
                            <template v-if="item.recommended_irrigation_mm > 0">
                                <span class="app-mono text-2xl font-bold text-ink tracking-tight">{{ item.recommended_irrigation_mm }}</span>
                                <span class="text-sm font-semibold text-muted"> mm</span>
                            </template>
                            <span v-else class="text-sm font-bold text-soft">Sin riego</span>
                        </div>
                    </div>
                    <!-- nivel 2: urgencia · déficit -->
                    <div class="flex items-center gap-3">
                        <span
                            class="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full shrink-0"
                            :style="{ background: urg(item.urgency).bg, color: urg(item.urgency).fg }"
                        >
                            <span class="w-1.5 h-1.5 rounded-full" :style="{ background: urg(item.urgency).dot }"></span>
                            {{ URGENCY_LABEL[item.urgency] }}
                        </span>
                        <div class="flex-1 flex items-center gap-2">
                            <div class="flex-1 h-1.5 rounded-full bg-chip overflow-hidden">
                                <div class="h-full rounded-full" :style="{ width: deficitPct(item) + '%', background: deficitColor(deficitPct(item)) }"></div>
                            </div>
                            <span class="app-mono text-xs font-bold text-muted w-9 text-right">{{ deficitPct(item) }}%</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- DESKTOP -->
            <div class="hidden md:block space-y-2">
                <div
                    v-for="item in history"
                    :key="item.id"
                    class="bg-surface rounded-2xl border border-line shadow-sm px-4 py-3 flex items-center justify-between"
                >
                    <span class="text-sm text-muted w-24 shrink-0">{{ item.date }}</span>

                    <span
                        class="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full"
                        :style="{ background: urg(item.urgency).bg, color: urg(item.urgency).fg }"
                    >
                        <span class="w-1.5 h-1.5 rounded-full" :style="{ background: urg(item.urgency).dot }"></span>
                        {{ URGENCY_LABEL[item.urgency] }}
                    </span>

                    <span class="text-xs text-soft w-16 text-center">
                        {{ item.taw_mm ? deficitPct(item) + '% déf.' : '—' }}
                    </span>

                    <span class="text-sm font-bold text-ink w-16 text-right">
                        {{ item.recommended_irrigation_mm > 0 ? item.recommended_irrigation_mm + ' mm' : 'Sin riego' }}
                    </span>
                </div>
            </div>
        </template>

    </div>
</template>

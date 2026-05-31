<script setup>
import { ref, onMounted, computed} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Line } from 'vue-chartjs'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js'
import { getSectorChartData } from '../services/sectors'
import { ArrowLeft } from 'lucide-vue-next'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const rawData = ref(null)

onMounted(async () => {
    try {
        rawData.value = await getSectorChartData(route.params.id)
    } catch {
        error.value = 'No se pudo cargar el gráfico'
    } finally {
        loading.value = false
    }
})

const hasData = computed(() =>
    rawData.value && (rawData.value.deficit.length > 0 || rawData.value.ndvi.length > 0)
)

const deficitChartData = computed(() => {
    if (!rawData.value) return null
    const labels = rawData.value.deficit.map(d => d.date)
    return {
        labels,
        datasets: [
            {
                label: 'Déficit hídrico (%)',
                data: rawData.value.deficit.map(d => d.pct),
                borderColor: '#e65100',
                backgroundColor: 'rgba(230, 81, 0, 0.1)',
                tension: 0.3,
                fill: true,
            },
            {
                label: 'Umbral de estrés (RAW)',
                data: labels.map(() => rawData.value.raw_threshold_pct),
                borderColor: '#999',
                borderDash: [6, 4],
                borderWidth: 1.5,
                pointRadius: 0,
                fill: false,
            },
        ],
    }
})

const deficitOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
    scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } } },
        y: {
            min: 0, max: 100,
            title: { display: true, text: 'Déficit (%)' },
            ticks: { color: '#e65100' },
        },
    },
}

const ndviChartData = computed(() => {
    if (!rawData.value) return null
    return {
        labels: rawData.value.ndvi.map(d => d.date),
        datasets: [
            {
                label: 'NDVI',
                data: rawData.value.ndvi.map(d => d.value),
                borderColor: '#2e7d32',
                backgroundColor: 'rgba(46, 125, 50, 0.1)',
                tension: 0.3,
                pointRadius: 5,
                fill: true,
            },
        ],
    }
})

const ndviOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
    scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } } },
        y: {
            min: 0, max: 1,
            title: { display: true, text: 'NDVI' },
            ticks: { color: '#2e7d32' },
        },
    },
}
</script>

<template>
    <div class="max-w-2xl lg:max-w-3xl mx-auto px-4 py-6">

        <div class="flex items-center gap-3 mb-5">
            <button
                @click="router.push(`/sectors/${route.params.id}/history`)"
                class="flex items-center gap-1 text-green-800 font-semibold text-sm hover:underline"
            >
                <ArrowLeft class="w-4 h-4" />
                Historial
            </button>
            <h1 class="text-base font-bold text-gray-900">Evolución del cultivo</h1>
        </div>

        <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">Cargando gráfico...</div>
        <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>
        <div v-else-if="!hasData" class="text-center py-12 text-gray-400 text-sm">Sin datos suficientes para mostrar el gráfico.</div>

        <div v-else class="space-y-6">
            <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-4">
                <p class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3">Déficit hídrico</p>
                <div class="h-64 lg:h-96">
                    <Line :data="deficitChartData" :options="deficitOptions" />
                </div>
            </div>
            <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-4">
                <p class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3">NDVI — Vigor del cultivo</p>
                <div class="h-64 lg:h-96">
                    <Line :data="ndviChartData" :options="ndviOptions" />
                </div>
            </div>
        </div>

    </div>
</template>
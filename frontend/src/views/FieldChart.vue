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
import { getFieldChartData } from '../services/fields';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const rawData = ref(null)

onMounted(async () => {
    try {
        rawData.value = await getFieldChartData(route.params.id)
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
    plugins: { legend: { position: 'top' } },
    scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 11 } } },
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
    plugins: { legend: { position: 'top' } },
    scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 11 } } },
        y: {
            min: 0, max: 1,
            title: { display: true, text: 'NDVI' },
            ticks: { color: '#2e7d32' },
        },
    },
}
</script>

<template>
    <div class="chart-page">
        <header class="chart-header">
            <button class="btn-back" @click="router.push(`/fields/${route.params.id}/history`)"> <- Historial</button>
            <h1>Evolucion del cultivo</h1>
        </header>

        <div v-if="loading" class="center">Cargando gráfico...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else-if="!hasData" class="center">Sin datos suficientes para mostrar el grafico.</div>

        <div v-else>
            <div class="chart-wrap">
                <h2 class="chart-title">Déficit hídrico</h2>
                <Line :data="deficitChartData" :options="deficitOptions" />
            </div>
            <div class="chart-wrap">
                <h2 class="chart-title">NDVI (vigor del cultivo)</h2>
                <Line :data="ndviChartData" :options="ndviOptions" />
            </div>
        </div>
    </div>
</template>

<style scoped>
.chart-page {
    max-width: 700px;
    margin: 0 auto;
    padding: 1rem;
    font-family: sans-serif;
}
.chart-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.chart-header h1 { font-size: 1.2rem; margin: 0; color: #2e7d32; }
.btn-back {
    background: none;
    border: none;
    color: #2e7d32;
    font-size: 0.95rem;
    cursor: pointer;
    padding: 0;
}
.chart-wrap {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
}
.center { text-align: center; padding: 2rem; color: #666; }
.error { color: #c00; text-align: center; padding: 1rem; }
.chart-wrap { margin-bottom: 1rem; }
.chart-title {
    font-size: 0.95rem;
    color: #444;
    margin: 0 0 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
</style>
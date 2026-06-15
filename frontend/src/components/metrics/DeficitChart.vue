<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import '../../utils/chartSetup'
import { Activity } from 'lucide-vue-next'

const props = defineProps({
    daily: { type: Array, default: () => [] },
    rawThreshold: { type: Number, required: true },
})

const chartData = computed(() => {
    if (!props.daily.length) return null
    const labels = props.daily.map((d) => d.date)
    return {
        labels,
        datasets: [
            {
                label: 'Déficit del suelo (%)',
                data: props.daily.map((d) => d.deficit_pct),
                borderColor: '#D8651C',
                backgroundColor: 'rgba(216,101,28,0.10)',
                tension: 0.3, fill: true, pointRadius: 0, borderWidth: 2,
            },
            {
                label: 'Umbral de estrés (RAW)',
                data: labels.map(() => props.rawThreshold),
                borderColor: '#9CA3AF',
                borderDash: [6, 4], borderWidth: 1.5, pointRadius: 0, fill: false,
            },
        ],
    }
})

const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } } },
    scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } } },
        y: { min: 0, max: 100, title: { display: true, text: 'Déficit (%)' }, ticks: { font: { size: 10 } } },
    },
}
</script>

<template>
    <div v-if="chartData" class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-1 flex items-center gap-1.5"><Activity :size="13" /> Balance hídrico del suelo</div>
        <p class="text-xs text-soft mb-3 leading-relaxed">
            El déficit sube cuando el suelo se seca. Al cruzar la línea de estrés (RAW), la planta empieza a sufrir.
        </p>
        <div class="h-56 md:h-72"><Line :data="chartData" :options="options" /></div>
    </div>
</template>
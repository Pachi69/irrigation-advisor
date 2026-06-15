<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import '../../utils/chartSetup'
import { Satellite } from 'lucide-vue-next'

const props = defineProps({
    series: { type: Array, default: () => [] },
})

const chartData = computed(() => {
    if (!props.series.length) return null
    return {
        labels: props.series.map((d) => d.date),
        datasets: [
            {
                label: 'NDVI',
                data: props.series.map((d) => d.value),
                borderColor: '#2E7D32',
                backgroundColor: 'rgba(46,125,50,0.10)',
                tension: 0.3, pointRadius: 4, fill: true, borderWidth: 2,
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
        y: { min: 0, max: 1, title: { display: true, text: 'NDVI' }, ticks: { font: { size: 10 } } },
    },
}
</script>

<template>
    <div v-if="chartData" class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-1 flex items-center gap-1.5"><Satellite :size="13" /> NDVI — vigor del cultivo</div>
        <p class="text-xs text-soft mb-3 leading-relaxed">
            Testigo independiente: si el vigor se sostiene, el cultivo estuvo sano.
        </p>
        <div class="h-56 md:h-72"><Line :data="chartData" :options="options" /></div>
    </div>
</template>
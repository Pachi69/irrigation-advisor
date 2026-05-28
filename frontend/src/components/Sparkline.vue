<script setup>
/**
 * Sparkline.vue — mini-gráfico de línea para mostrar tendencia (déficit, NDVI).
 *
 * Props:
 *   - data: number[]
 *   - color: CSS color (string)
 *   - width / height: px
 */
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, required: true },
  color: { type: String, default: 'var(--color-primary)' },
  width: { type: Number, default: 80 },
  height: { type: Number, default: 24 },
})

const pts = computed(() => {
  const max = Math.max(...props.data)
  const min = Math.min(...props.data)
  const range = max - min || 1
  return props.data.map((v, i) => {
    const x = (i / (props.data.length - 1)) * props.width
    const y = props.height - ((v - min) / range) * props.height
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
})

const lastPoint = computed(() => {
  const max = Math.max(...props.data)
  const min = Math.min(...props.data)
  const range = max - min || 1
  const v = props.data[props.data.length - 1]
  return {
    x: props.width,
    y: props.height - ((v - min) / range) * props.height,
  }
})
</script>

<template>
  <svg :width="width" :height="height" :viewBox="`0 0 ${width} ${height}`" class="overflow-visible">
    <polyline
      :points="pts"
      fill="none" :stroke="color" stroke-width="1.8"
      stroke-linecap="round" stroke-linejoin="round"
    />
    <circle :cx="lastPoint.x" :cy="lastPoint.y" r="2.5" :fill="color" />
  </svg>
</template>

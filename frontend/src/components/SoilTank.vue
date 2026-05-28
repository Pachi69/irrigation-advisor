<script setup>
/**
 * SoilTank.vue
 * Visualización vertical del agua disponible en el suelo, con marca de umbral RAW.
 * El color de relleno cambia según urgencia.
 *
 * Props:
 *   - deficitPct: 0..100 (100 = totalmente seco)
 *   - raw: % del umbral de estrés (default 50)
 */
import { computed } from 'vue'

const props = defineProps({
  deficitPct: { type: Number, required: true },
  raw: { type: Number, default: 50 },
})

const availablePct = computed(() => 100 - props.deficitPct)

const fillColor = computed(() => {
  const d = props.deficitPct
  if (d >= 75) return 'var(--color-rust)'
  if (d >= 50) return '#D8651C'
  if (d >= 30) return 'var(--color-amber)'
  return 'var(--color-water)'
})
</script>

<template>
  <div class="flex items-stretch gap-3.5">
    <!-- Tank -->
    <div class="relative w-14 h-36 rounded-lg overflow-hidden bg-chip border border-line">
      <div
        class="absolute bottom-0 left-0 right-0 transition-[height] duration-500"
        :style="{ height: availablePct + '%', background: fillColor }"
      >
        <div class="absolute top-0 inset-x-0 h-[3px] bg-white/40" />
      </div>
      <div
        class="absolute -left-1 -right-1 border-t border-dashed border-black/35 h-0"
        :style="{ bottom: raw + '%' }"
      />
    </div>

    <!-- Labels -->
    <div class="flex-1 flex flex-col justify-between py-0.5">
      <div>
        <div class="app-label">Capacidad</div>
        <div class="app-mono text-[13px] font-semibold text-muted">FC</div>
      </div>
      <div class="border-l border-dashed border-soft pl-2 -ml-2">
        <div class="app-label">Umbral estrés</div>
        <div class="app-mono text-[13px] font-semibold text-muted">RAW</div>
      </div>
      <div>
        <div class="app-label">Disponible</div>
        <div class="app-mono text-base font-bold text-ink">{{ availablePct }}%</div>
      </div>
    </div>
  </div>
</template>

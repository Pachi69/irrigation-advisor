<script setup>
/**
 * UrgencyHero.vue — la tarjeta central de Recomendación.
 * Fondo negro con número enorme de mm cuando hay que regar; fondo verde-suave cuando no.
 *
 * Props:
 *   - mm:          number — milímetros recomendados
 *   - urgency:     'none' | 'low' | 'medium' | 'high' | 'critical'
 *   - reason:      string — razón / contexto
 *   - dateLabel:   string — "martes 25 mayo"
 *   - confidence:  string — "Alta · 92%"
 *   - areaHa:      number — para calcular m³
 */
import { computed } from 'vue'
import { Droplet } from 'lucide-vue-next'

const props = defineProps({
  mm: { type: Number, required: true },
  urgency: { type: String, default: 'low' },
  reason: { type: String, default: '' },
  dateLabel: { type: String, default: '' },
  confidence: { type: String, default: 'Alta · 90%' },
  areaHa: { type: Number, default: 1 },
})

const needsIrrigation = computed(() => props.mm > 0)

const urgencyLabel = computed(() => ({
  none: 'Sin urgencia', low: 'Urgencia baja',
  medium: 'Urgencia moderada', high: 'Urgencia alta',
  critical: 'Crítico',
}[props.urgency] || 'Sin urgencia'))

const urgencyDot = computed(() => ({
  none: 'bg-primary', low: 'bg-primary',
  medium: 'bg-amber', high: 'bg-amber',
  critical: 'bg-rust',
}[props.urgency] || 'bg-primary'))

const volumeM3 = computed(() => Math.round(props.mm * props.areaHa * 10))
</script>

<template>
  <div
    class="relative overflow-hidden rounded-3xl px-6 py-7"
    :class="needsIrrigation ? 'bg-ink text-white' : 'bg-primary-soft text-primary'"
  >
    <!-- Meta row -->
    <div class="flex justify-between items-center text-[11px] font-bold uppercase tracking-wider mb-3.5"
         :class="needsIrrigation ? 'text-white/70' : 'text-primary/70'">
      <span>{{ dateLabel }}</span>
      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full"
            :class="needsIrrigation ? 'bg-white/12' : 'bg-black/5'">
        <span class="w-1.5 h-1.5 rounded-full" :class="urgencyDot" />
        {{ urgencyLabel }}
      </span>
    </div>

    <!-- Action label -->
    <div class="text-lg font-bold tracking-tight mb-0.5 opacity-90">
      {{ needsIrrigation ? 'REGAR' : 'NO REGAR' }}
    </div>

    <!-- Massive number -->
    <div class="app-display flex items-baseline justify-start gap-1.5" style="font-size: 108px">
      {{ mm }}<span class="text-[38px] font-semibold tracking-tight">mm</span>
    </div>

    <!-- Subtitle -->
    <p class="text-[13.5px] leading-snug mt-2 pr-2"
       :class="needsIrrigation ? 'text-white/85' : 'text-primary/85'">
      {{ reason }}
    </p>

    <!-- Footer chips -->
    <div class="flex gap-3 mt-4 pt-3.5"
         :class="needsIrrigation ? 'border-t border-white/12' : 'border-t border-black/8'">
      <div v-if="needsIrrigation" class="flex-1">
        <div class="text-[10px] opacity-60 font-bold uppercase tracking-wider">Volumen aprox.</div>
        <div class="app-mono text-[15px] font-bold">{{ volumeM3 }} m³</div>
      </div>
      <div class="flex-1">
        <div class="text-[10px] opacity-60 font-bold uppercase tracking-wider">Confianza</div>
        <div class="text-sm font-bold">{{ confidence }}</div>
      </div>
    </div>

    <!-- Decorative drop -->
    <Droplet
      class="absolute -top-10 -right-10 pointer-events-none"
      :class="needsIrrigation ? 'opacity-5' : 'opacity-10'"
      :size="180" :stroke-width="1.5"
    />
  </div>
</template>

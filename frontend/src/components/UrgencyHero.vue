<script setup>
/**
 * UrgencyHero.vue — la tarjeta central de Recomendación.
 * Formato "objetivo total": el protagonista es la lamina a reponer (mm).
 * El tiempo y el volumen acompanan como equivalencias. El tiempo solo
 * aparece si el sector tiene caudal cargado; si no, se invita a cargarlo.
 *
 * Props:
 *   - mm:          number — lamina neta recomendada (mm), protagonista
 *   - timeMin:     number | null — tiempo de riego total (min)
 *   - volumeM3:    number | null — volumen bruto (m3)
 *   - urgency:     'none' | 'low' | 'medium' | 'high' | 'critical'
 *   - reason:      string
 *   - dateLabel:   string
 *   - confidence:  string
*/
import { computed } from 'vue'
import { Droplet } from 'lucide-vue-next'
import { formatMinutes } from '../utils/format'

const props = defineProps({
  mm: { type: Number, required: true },
  timeMin: { type: Number, default: null },
  volumeM3: { type: Number, default: null },
  urgency: { type: String, default: 'low' },
  reason: { type: String, default: '' },
  dateLabel: { type: String, default: '' },
  confidence: { type: String, default: 'Alta · 90%' },
})

const needsIrrigation = computed(() => props.mm > 0)
const hasTime = computed(() => props.timeMin != null)

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

const timeLabel = computed(() => props.timeMin != null ? formatMinutes(props.timeMin) : '-')
const volumeLabel = computed(() => props.volumeM3 != null ? Math.round(props.volumeM3) : null)
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
        {{ needsIrrigation ? 'REPONER' : 'NO REGAR' }}
      </div>

      <!-- Massive number: Tiempo si hay caudal, sino volumen -->
      <template v-if="needsIrrigation">
        <div class="app-display flex items-baseline justify-start gap-1.5" style="font-size: 84px">
          <template v-if="hasTime">{{ timeLabel }}</template>
          <template v-else-if="volumeLabel != null">
            {{ volumeLabel }}<span class="text-[32px] font-semibold tracking-tight"> m³</span>
          </template>
          
        </div>

        <!-- Equivalencias: tiempo total + volumen -->
        <div class="app-mono text-sm font-semibold mt-1 opacity-80">
          <template v-if="hasTime && volumeLabel != null">~{{ volumeLabel }} m³ · </template>
          {{ mm }}<span class="text-[14px] font-semibold tracking-tight"> mm de lamina</span>
        </div>

        <!-- Aviso cuando falta el caudal -->
        <div v-if="!hasTime" class="text-[12.5px] font-medium mt-1.5 opacity-75">
          Cargá el caudal de tu bomba para calcular el tiempo de riego.
        </div>
      </template>

      <div v-else class="app-display flex items-baseline justify-start gap-1.5" style="font-size: 84px">
        0<span class="text-[32px] font-semibold tracking-tight">mm</span>
      </div>

      <!-- Subtitle: razon del balance -->
      <p class="text-[13.5px] leading-snug mt-2 pr-2"
         :class="needsIrrigation ? 'text-white/85' : 'text-primary/85'">
        {{ reason }}
      </p>

      <!-- Nota de reparto -->
      <p v-if="needsIrrigation" class="text-[12.5px] leading-snug mt-1.5 opacity-70">
        Es el total a reponer. Podés repartirlo en uno o varios riegos según tu turno de agua.
      </p>

      <!-- Footer chips -->
      <div class="flex gap-3 mt-4 pt-3.5"
           :class="needsIrrigation ? 'border-t border-white/12' : 'border-t border-black/8'">
        <div v-if="needsIrrigation" class="flex-1">
          <div class="text-[10px] opacity-60 font-bold uppercase tracking-wider">Tiempo total</div>
          <div class="app-mono text-[15px] font-bold">{{ hasTime ? timeLabel : 'Sin caudal' }}</div>
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
<script setup>
/**
 * Home.vue — Dashboard del productor.
 * Razona sobre sectores (la unidad de riego); el campo es contenedor.
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuth } from '../stores/auth'
import { listMyFields } from '../services/fields'
import { requestPushPermission, subscribeToPush } from '../services/push'
import { ArrowRight, Plus, Bell, Satellite } from 'lucide-vue-next'
import { CROP_LABELS } from '../utils/labels'
import Sparkline from '../components/Sparkline.vue'

const router = useRouter()
const { user } = useAuth()

const fields = ref([])
const loading = ref(true)
const pushStatus = ref('idle')

const todayLabel = computed(() => {
  const d = new Date()
  const day = d.toLocaleDateString('es-AR', { weekday: 'short' })
  const date = d.toLocaleDateString('es-AR', { day: 'numeric', month: 'long' })
  return `${day.replace('.', '')} · ${date} · San Rafael`
})

const activeFields = computed(() => fields.value.filter(f => f.status === 'active'))

// Todos los sectores de campos activos, con el nombre del campo embebido
const activeSectors = computed(() =>
  activeFields.value.flatMap(f =>
    (f.sectors || []).map(s => ({ ...s, fieldName: f.name }))
  )
)

const totalArea = computed(() =>
  activeSectors.value.reduce((s, sec) => s + (sec.area_ha || 0), 0).toFixed(1)
)

// Sector más urgente que necesita riego HOY
const urgentSector = computed(() => {
  const withRec = activeSectors.value.filter(
    s => s.last_recommendation && ['high', 'critical'].includes(s.last_recommendation.urgency)
  )
  return withRec.sort((a, b) =>
    b.last_recommendation.recommended_irrigation_mm - a.last_recommendation.recommended_irrigation_mm
  )[0] || null
})

const urgentCount = computed(() => activeSectors.value.filter(
  s => s.last_recommendation && ['high', 'critical', 'medium'].includes(s.last_recommendation.urgency)
).length)

async function load() {
  try {
    fields.value = await listMyFields()
  } finally {
    loading.value = false
  }
}

async function enableNotifications() {
  pushStatus.value = 'requesting'
  const granted = await requestPushPermission()
  if (!granted) { pushStatus.value = 'denied'; return }
  try { await subscribeToPush(); pushStatus.value = 'granted' }
  catch { pushStatus.value = 'error' }
}

function urgencyDot(u) {
  return {
    critical: 'bg-rust', high: 'bg-amber',
    medium: 'bg-amber', low: 'bg-primary', none: 'bg-soft',
  }[u] || 'bg-soft'
}

function urgencyColor(u) {
  return {
    critical: 'var(--color-rust)', high: 'var(--color-rust)',
    medium: 'var(--color-amber)', low: 'var(--color-primary)', none: 'var(--color-soft)',
  }[u] || 'var(--color-primary)'
}

onMounted(() => {
  load()
  if ('Notification' in window) {
    if (Notification.permission === 'granted') pushStatus.value = 'granted'
    else if (Notification.permission === 'denied') pushStatus.value = 'denied'
  }
})
</script>

<template>
  <div class="max-w-[1180px] mx-auto px-5 md:px-8 pt-3 md:pt-8 pb-8">

    <!-- Header -->
    <div class="flex justify-between items-start md:items-end mb-5 md:mb-7">
      <div>
        <div class="app-label mb-1">{{ todayLabel }}</div>
        <h1 class="text-[26px] md:text-[38px] font-bold text-ink tracking-tight leading-tight m-0">
          Hola, {{ user?.name || 'Productor' }}.
        </h1>
      </div>
    </div>

    <!-- Push activation banner (solo si idle) -->
    <div v-if="pushStatus === 'idle'" class="mb-4 bg-amber-soft border border-amber/30 rounded-2xl p-4 flex items-center gap-3">
      <div class="w-9 h-9 rounded-xl bg-amber text-white flex items-center justify-center shrink-0">
        <Bell :size="18" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="text-sm font-bold text-ink">Activá las alertas de riego</div>
        <div class="text-xs text-muted">Te avisamos cuando hay que regar.</div>
      </div>
      <button @click="enableNotifications" class="bg-amber text-white text-sm font-bold px-3 py-2 rounded-xl shrink-0">
        Activar
      </button>
    </div>

    <!-- ─── Two-column on desktop · single column on mobile ─── -->
    <div class="grid md:grid-cols-[1.4fr_1fr] gap-4 mb-7">

      <!-- Today's action — hero card -->
      <div class="relative overflow-hidden bg-ink text-white rounded-3xl p-6 md:p-7 min-h-[180px] md:min-h-[220px]">
        <div class="text-[11px] font-bold uppercase tracking-widest opacity-70 mb-2">
          Acción del día
        </div>

        <template v-if="urgentSector">
          <h2 class="text-xl md:text-[28px] font-bold tracking-tight leading-tight m-0 mb-1">
            {{ urgentCount }} {{ urgentCount === 1 ? 'sector necesita' : 'sectores necesitan' }} riego hoy
          </h2>
          <div class="text-sm opacity-70 mb-5 md:mb-6">
            <template v-if="activeSectors.length - urgentCount > 0">
              {{ activeSectors.length - urgentCount }}
              {{ (activeSectors.length - urgentCount) === 1 ? 'está' : 'están' }} dentro de rango.
            </template>
            <template v-else>
              Revisalos antes del mediodía.
            </template>
          </div>
          <div class="flex items-end justify-between gap-4 pt-4 md:pt-5 border-t border-white/12">
            <div>
              <div class="text-xs opacity-65 mb-1">{{ urgentSector.fieldName }} · {{ urgentSector.name }}</div>
              <div class="app-mono text-3xl md:text-[42px] font-bold tracking-tight leading-none">
                {{ urgentSector.last_recommendation.recommended_irrigation_mm.toFixed(0) }}<span class="text-base opacity-60 ml-1">mm</span>
              </div>
            </div>
            <RouterLink
              :to="`/sectors/${urgentSector.id}/recommendation`"
              class="bg-white text-ink font-bold text-sm px-4 py-2.5 rounded-xl inline-flex items-center gap-1.5"
            >
              Ver <ArrowRight :size="14" />
            </RouterLink>
          </div>
        </template>

        <template v-else-if="activeSectors.length === 0">
          <h2 class="text-xl md:text-[28px] font-bold tracking-tight leading-tight m-0 mb-1">
            Bienvenido a Irrigation Advisor.
          </h2>
          <div class="text-sm opacity-70 mb-5 md:mb-6">
            Registrá tu primer campo para empezar a recibir recomendaciones.
          </div>
          <RouterLink
            to="/fields/new"
            class="inline-flex items-center gap-1.5 bg-white text-ink font-bold text-sm px-4 py-2.5 rounded-xl"
          >
            <Plus :size="14" /> Registrar campo
          </RouterLink>
        </template>

        <template v-else>
          <h2 class="text-xl md:text-[28px] font-bold tracking-tight leading-tight m-0 mb-1">
            Todo en orden hoy.
          </h2>
          <div class="text-sm opacity-70">
            No se requiere riego en ninguno de tus campos.
          </div>
        </template>

        <!-- Decorative drop -->
        <svg class="absolute -top-10 -right-10 opacity-5 pointer-events-none" width="220" height="220" viewBox="0 0 32 32" fill="none">
          <path d="M16 3c-4 6-7 9-7 13a7 7 0 0 0 14 0c0-4-3-7-7-13z" fill="currentColor"/>
        </svg>
      </div>

      <!-- Summary (solo desktop, queda muy denso en mobile) -->
      <div class="hidden md:flex flex-col gap-3">
        <div class="bg-surface border border-line rounded-3xl px-5 py-4">
          <div class="app-label mb-2">Resumen</div>
          <div class="grid grid-cols-2 gap-3.5">
            <div>
              <div class="app-label">Campos activos</div>
              <div class="text-lg font-bold mt-1">{{ activeFields.length }}</div>
            </div>
            <div>
              <div class="app-label">Superficie total</div>
              <div class="app-mono text-lg font-bold mt-1">{{ totalArea }} <span class="text-sm text-muted font-semibold">ha</span></div>
            </div>
          </div>
        </div>
        <div class="bg-primary-soft rounded-3xl px-5 py-3.5 flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-primary text-white flex items-center justify-center shrink-0">
            <Satellite :size="18" />
          </div>
          <div class="flex-1">
            <div class="text-xs font-bold uppercase tracking-wide text-primary">Sentinel-2</div>
            <div class="text-sm font-medium">Datos de NDVI semanales</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Fields list -->
    <div class="flex items-center justify-between px-1 mb-2.5">
      <div class="app-label">Mis campos</div>
    </div>

    <div v-if="loading" class="text-center py-12 text-muted text-sm">Cargando...</div>
    <div v-else-if="fields.length === 0" class="bg-surface border border-line rounded-3xl p-6 text-center">
      <p class="text-muted text-sm mb-3">Aún no registraste tu primer campo.</p>
      <RouterLink to="/fields/new" class="inline-flex items-center gap-1.5 bg-primary text-white font-bold text-sm px-4 py-2.5 rounded-xl">
        <Plus :size="14" /> Registrar campo
      </RouterLink>
    </div>

    <div v-else class="grid md:grid-cols-2 gap-3">
      <RouterLink
        v-for="s in activeSectors" :key="s.id"
        :to="`/sectors/${s.id}/recommendation`"
        class="bg-surface border border-line rounded-2xl p-4 md:p-5 flex items-center gap-3 hover:border-soft transition-colors"
      >
        <span
          class="w-2 h-2 rounded-full shrink-0"
          :class="urgencyDot(s.last_recommendation?.urgency || 'none')"
        />
        <div class="flex-1 min-w-0">
          <div class="text-[15px] md:text-base font-bold text-ink tracking-tight truncate">{{ s.fieldName }} · {{ s.name }}</div>
          <div class="text-xs text-muted">{{ CROP_LABELS[s.crop_type] || s.crop_type }} · {{ s.area_ha?.toFixed(1) }} ha</div>
        </div>
        <Sparkline
          v-if="s.last_recommendation?.deficit_history?.length > 1"
          :data="s.last_recommendation.deficit_history"
          :color="urgencyColor(s.last_recommendation.urgency)"
          :width="60" :height="24"
        />
        <div class="app-mono text-base font-bold text-ink min-w-[60px] text-right">
          <template v-if="s.last_recommendation && s.last_recommendation.recommended_irrigation_mm > 0">
            {{ s.last_recommendation.recommended_irrigation_mm.toFixed(0) }} mm
          </template>
          <template v-else-if="s.last_recommendation">—</template>
          <span v-else class="text-xs text-muted font-normal">Sin datos</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
/**
 * FieldList.vue — Mis Campos
 *
 * Mobile: lista vertical de tarjetas (banner urgencia + nombre + cultivo + sparkline + mm + CTA).
 * Desktop: grid 3-col + chips de filtro.
 *
 * Usa los campos `last_recommendation` embebidos en FieldPublic.
 */
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { listMyFields } from '../services/fields'
import { Plus, ChevronRight, Clock } from 'lucide-vue-next'
import { CROP_LABELS, URGENCY_LABEL } from '../utils/labels'
import Sparkline from '../components/Sparkline.vue'

const fields = ref([])
const loading = ref(true)
const error = ref('')
const filter = ref('all')

async function load() {
  error.value = ''
  loading.value = true
  try { fields.value = await listMyFields() }
  catch { error.value = 'No se pudieron cargar los campos.' }
  finally { loading.value = false }
}

function urgency(f) {
  return f.last_recommendation?.urgency || 'none'
}

const filtered = computed(() => {
  if (filter.value === 'all') return fields.value
  if (filter.value === 'pending') return fields.value.filter(f => f.status === 'pending')
  if (filter.value === 'urgent') return fields.value.filter(
    f => f.last_recommendation && ['high', 'critical'].includes(f.last_recommendation.urgency)
  )
  return fields.value
})

const counts = computed(() => ({
  all: fields.value.length,
  active: fields.value.filter(f => f.status === 'active').length,
  pending: fields.value.filter(f => f.status === 'pending').length,
  urgent: fields.value.filter(
    f => f.last_recommendation && ['high', 'critical'].includes(f.last_recommendation.urgency)
  ).length,
}))

const totalArea = computed(() =>
  fields.value.filter(f => f.status === 'active')
    .reduce((s, f) => s + (f.area_ha || 0), 0).toFixed(1)
)

const hasPending = computed(() => fields.value.some(f => f.status === 'pending'))

function urgencyMeta(u) {
  return ({
    critical: { dot: 'bg-rust', text: 'text-rust',    color: 'var(--color-rust)' },
    high:     { dot: 'bg-amber', text: 'text-amber',  color: 'var(--color-rust)' },
    medium:   { dot: 'bg-amber', text: 'text-amber',  color: 'var(--color-amber)' },
    low:      { dot: 'bg-primary', text: 'text-primary', color: 'var(--color-primary)' },
    none:     { dot: 'bg-soft', text: 'text-muted',   color: 'var(--color-soft)' },
  })[u] || { dot: 'bg-soft', text: 'text-muted', color: 'var(--color-soft)' }
}

onMounted(load)
</script>

<template>
  <div class="max-w-[1180px] mx-auto px-5 md:px-8 pt-3 md:pt-8 pb-8">

    <!-- Header -->
    <div class="flex justify-between items-center mb-5 md:mb-6">
      <div>
        <h1 class="text-2xl md:text-3xl font-bold text-ink tracking-tight leading-tight">Mis campos</h1>
        <div class="hidden md:block text-sm text-muted mt-1">
          {{ counts.active }} {{ counts.active === 1 ? 'activo' : 'activos' }} · {{ totalArea }} ha · San Rafael, Mendoza
        </div>
      </div>
      <RouterLink
        v-if="!hasPending" to="/fields/new"
        class="inline-flex items-center gap-1.5 bg-primary text-primary-ink font-bold text-sm px-3.5 py-2.5 rounded-xl"
      >
        <Plus :size="15" /> <span class="hidden sm:inline">Nuevo campo</span><span class="sm:hidden">Nuevo</span>
      </RouterLink>
      <span v-else class="inline-flex items-center gap-1.5 bg-chip text-soft font-bold text-sm px-3.5 py-2.5 rounded-xl cursor-not-allowed">
        <Plus :size="15" /> Nuevo campo
      </span>
    </div>

    <!-- Filter pills (solo desktop) -->
    <div class="hidden md:flex gap-2 mb-5">
      <button
        v-for="f in [
          { id: 'all', label: `Todos · ${counts.all}` },
          { id: 'urgent', label: `Urgentes · ${counts.urgent}` },
          { id: 'pending', label: `Pendientes · ${counts.pending}` },
        ]" :key="f.id"
        @click="filter = f.id"
        class="px-3.5 py-2 rounded-full text-[13px] font-semibold border transition-colors"
        :class="filter === f.id ? 'bg-ink text-white border-ink' : 'bg-surface text-muted border-line'"
      >{{ f.label }}</button>
    </div>

    <!-- States -->
    <div v-if="loading" class="text-center py-12 text-muted text-sm">Cargando campos...</div>
    <div v-else-if="error" class="bg-rust-soft border border-rust/20 text-rust text-sm font-medium px-4 py-3 rounded-2xl">{{ error }}</div>
    <div v-else-if="filtered.length === 0" class="bg-surface border border-line rounded-3xl p-8 text-center">
      <p class="text-muted text-sm mb-3">No tenés campos registrados.</p>
      <RouterLink to="/fields/new" class="inline-flex items-center gap-1.5 bg-primary text-white font-bold text-sm px-4 py-2.5 rounded-xl">
        <Plus :size="14" /> Registrá el primero
      </RouterLink>
    </div>

    <!-- Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4">

      <template v-for="f in filtered" :key="f.id">
        <!-- Pending -->
        <div v-if="f.status === 'pending'" class="bg-surface border-[1.5px] border-dashed border-line rounded-2xl p-5">
          <div class="flex items-center gap-1.5 mb-1.5 text-muted">
            <Clock :size="13" />
            <span class="text-[10px] font-bold uppercase tracking-wider">Pendiente de aprobación</span>
          </div>
          <div class="text-base font-bold text-ink tracking-tight">{{ f.name }}</div>
          <div class="text-[13px] text-muted mb-2.5">
            {{ CROP_LABELS[f.crop_type] || f.crop_type }} · {{ f.area_ha?.toFixed(1) }} ha
          </div>
          <div class="text-xs text-muted leading-relaxed">
            Un administrador revisará tu campo en las próximas 24 hs.
          </div>
        </div>

        <!-- Active -->
        <RouterLink
          v-else :to="`/fields/${f.id}/recommendation`"
          class="bg-surface border border-line rounded-2xl overflow-hidden flex flex-col hover:border-soft transition-colors"
        >
          <div class="px-4 pt-4 pb-3 flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1.5 mb-1">
                <span class="w-2 h-2 rounded-full" :class="urgencyMeta(urgency(f)).dot" />
                <span class="text-[10px] font-bold uppercase tracking-wider" :class="urgencyMeta(urgency(f)).text">
                  {{ URGENCY_LABEL[urgency(f)] || 'Sin datos' }}
                </span>
              </div>
              <div class="text-base md:text-lg font-bold text-ink tracking-tight">{{ f.name }}</div>
              <div class="text-[13px] text-muted mt-0.5">
                {{ CROP_LABELS[f.crop_type] || f.crop_type }} · {{ f.area_ha?.toFixed(1) }} ha
              </div>
            </div>
            <Sparkline
              v-if="f.last_recommendation?.deficit_history?.length > 1"
              :data="f.last_recommendation.deficit_history"
              :color="urgencyMeta(urgency(f)).color"
              :width="70" :height="28"
            />
          </div>

          <div class="px-4 py-3 border-t border-line flex items-center justify-between bg-chip">
            <div>
              <div class="app-label">Hoy</div>
              <div class="app-mono text-lg font-bold text-ink mt-0.5">
                <template v-if="f.last_recommendation && f.last_recommendation.recommended_irrigation_mm > 0">
                  {{ f.last_recommendation.recommended_irrigation_mm.toFixed(0) }} mm
                </template>
                <template v-else-if="f.last_recommendation">Sin riego</template>
                <span v-else class="text-sm text-muted font-normal">Sin datos</span>
              </div>
            </div>
            <span class="inline-flex items-center gap-1 text-sm font-bold text-primary">
              Abrir <ChevronRight :size="14" />
            </span>
          </div>
        </RouterLink>
      </template>

    </div>
  </div>
</template>

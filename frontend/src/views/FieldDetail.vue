<script setup>
import { ref, onMounted, computed} from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { getFieldById, deleteField } from '../services/fields'
import { Plus, ChevronRight, ArrowLeft, Sprout, Pencil, Trash2 } from 'lucide-vue-next'
import { CROP_LABELS, SOIL_LABELS, STATUS_LABELS, URGENCY_LABEL } from '../utils/labels'
import Sparkline from '../components/Sparkline.vue'

const route = useRoute()
const router = useRouter()

const field = ref(null)
const loading = ref(true)
const error = ref('')

async function load() {
    loading.value = true
    error.value = ''
    try {
        field.value = await getFieldById(route.params.id)
    } catch {
        error.value = 'No se pudo cargar el campo'
    } finally {
        loading.value = false
    }
}

const sectors = computed(() => field.value?.sectors || [])
const isActive = computed(() => field.value?.status === 'active') 

function urgencyMeta(u) {
  return ({
    critical: { dot: 'bg-rust', text: 'text-rust', color: 'var(--color-rust)' },
    high:     { dot: 'bg-amber', text: 'text-amber', color: 'var(--color-rust)' },
    medium:   { dot: 'bg-amber', text: 'text-amber', color: 'var(--color-amber)' },
    low:      { dot: 'bg-primary', text: 'text-primary', color: 'var(--color-primary)' },
    none:     { dot: 'bg-soft', text: 'text-muted', color: 'var(--color-soft)' },
  })[u] || { dot: 'bg-soft', text: 'text-muted', color: 'var(--color-soft)' }
}

async function handleDelete() {
  if (!confirm('¿Eliminar este campo y todos sus sectores? Esta acción no se puede deshacer.')) return
  try {
    await deleteField(route.params.id)
    router.push('/fields')
  } catch {
    error.value = 'No se pudo eliminar el campo.'
  }
}

onMounted(load)
</script>

<template>
  <div class="max-w-[1180px] mx-auto px-4 md:px-8 pt-2 md:pt-6 pb-8">

    <!-- Back -->
    <div class="flex items-center justify-between mb-4 md:mb-5 gap-2">
      <button @click="router.push('/fields')" class="flex items-center gap-1.5 text-primary font-semibold text-sm">
        <ArrowLeft :size="16" />
        <span class="hidden md:inline">Mis campos</span>
        <span class="md:hidden">Volver</span>
      </button>
      <div class="flex items-center gap-2">
        <RouterLink :to="`/fields/${route.params.id}/edit`" class="flex items-center gap-1 text-xs md:text-sm font-semibold text-ink border border-line bg-surface px-3 py-1.5 rounded-xl">
          <Pencil :size="13" /> Editar
        </RouterLink>
        <button @click="handleDelete" class="flex items-center gap-1 text-xs md:text-sm font-semibold text-rust border border-rust/20 bg-rust-soft px-3 py-1.5 rounded-xl">
          <Trash2 :size="13" /> Eliminar
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-muted text-sm">Cargando campo...</div>
    <div v-else-if="error" class="bg-rust-soft border border-rust/20 text-rust text-sm font-medium px-4 py-3 rounded-2xl">{{ error }}</div>

    <template v-else-if="field">
      <!-- Title -->
      <h1 class="text-2xl md:text-3xl font-bold text-ink tracking-tight leading-tight mb-1">{{ field.name }}</h1>
      <div class="text-sm text-muted mb-1">
        <template v-if="field.soil_type">{{ SOIL_LABELS[field.soil_type] || field.soil_type }} · </template>
        {{ sectors.length }} {{ sectors.length === 1 ? 'sector' : 'sectores' }}
      </div>
      <div class="mb-5 md:mb-6">
        <span
          class="inline-block text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full"
          :class="isActive ? 'bg-primary-soft text-primary' : 'bg-chip text-muted'"
        >{{ STATUS_LABELS[field.status] || field.status }}</span>
      </div>

      <!-- Pending notice -->
      <div v-if="!isActive" class="bg-blue-50 border border-blue-200 text-blue-700 text-sm px-4 py-3 rounded-2xl mb-5">
        Agregá los sectores de tu campo. Un administrador lo revisará y aprobará para empezar a recibir recomendaciones.
      </div>

      <!-- Sectores header -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-bold text-ink">Sectores</h2>
        <RouterLink
          :to="`/fields/${route.params.id}/sectors/new`"
          class="inline-flex items-center gap-1.5 bg-primary text-primary-ink font-bold text-sm px-3.5 py-2.5 rounded-xl"
        >
          <Plus :size="15" /> Agregar sector
        </RouterLink>
      </div>

      <!-- Empty sectors -->
      <div v-if="sectors.length === 0" class="bg-surface border border-line rounded-3xl p-8 text-center">
        <Sprout :size="28" class="mx-auto text-soft mb-2" />
        <p class="text-muted text-sm mb-3">Este campo todavía no tiene sectores.</p>
        <RouterLink :to="`/fields/${route.params.id}/sectors/new`" class="inline-flex items-center gap-1.5 bg-primary text-white font-bold text-sm px-4 py-2.5 rounded-xl">
          <Plus :size="14" /> Agregar el primero
        </RouterLink>
      </div>

      <!-- Sectores grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
        <RouterLink
          v-for="s in sectors" :key="s.id"
          :to="isActive ? `/sectors/${s.id}/recommendation` : `/sectors/${s.id}/edit`"
          class="bg-surface border border-line rounded-2xl overflow-hidden flex flex-col hover:border-soft transition-colors"
        >
          <div class="px-4 pt-4 pb-3 flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1.5 mb-1">
                <span class="w-2 h-2 rounded-full" :class="urgencyMeta(s.last_recommendation?.urgency || 'none').dot" />
                <span class="text-[10px] font-bold uppercase tracking-wider" :class="urgencyMeta(s.last_recommendation?.urgency || 'none').text">
                  {{ URGENCY_LABEL[s.last_recommendation?.urgency || 'none'] }}
                </span>
              </div>
              <div class="text-base md:text-lg font-bold text-ink tracking-tight">{{ s.name }}</div>
              <div class="text-[13px] text-muted mt-0.5">
                {{ CROP_LABELS[s.crop_type] || s.crop_type }}<template v-if="s.variety"> · {{ s.variety }}</template> · {{ s.area_ha?.toFixed(1) }} ha
              </div>
            </div>
            <Sparkline
              v-if="s.last_recommendation?.deficit_history?.length > 1"
              :data="s.last_recommendation.deficit_history"
              :color="urgencyMeta(s.last_recommendation?.urgency || 'none').color"
              :width="70" :height="28"
            />
          </div>
          <div class="px-4 py-3 border-t border-line flex items-center justify-between bg-chip">
            <div>
              <div class="app-label">Hoy</div>
              <div class="app-mono text-lg font-bold text-ink mt-0.5">
                <template v-if="s.last_recommendation && s.last_recommendation.recommended_irrigation_mm > 0">
                  {{ s.last_recommendation.recommended_irrigation_mm.toFixed(0) }} mm
                </template>
                <template v-else-if="s.last_recommendation">Sin riego</template>
                <span v-else class="text-sm text-muted font-normal">Sin datos</span>
              </div>
            </div>
            <span class="inline-flex items-center gap-1 text-sm font-bold text-primary">
              {{ isActive ? 'Abrir' : 'Configurar' }} <ChevronRight :size="14" />
            </span>
          </div>
        </RouterLink>
      </div>
    </template>
  </div>
</template>
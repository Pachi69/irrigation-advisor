<script setup> 
import { ref, onMounted } from 'vue'
import { listPendingSectors, approveSector, adminUpdateSector } from '../services/admin'
import FieldMapEditor from '../components/FieldMapEditor.vue'
import { RefreshCw, MapPin, Check } from 'lucide-vue-next'
import { CROP_LABELS } from '../utils/labels'


const fields = ref([])
const loading = ref(true)
const error = ref('')

const editingSector = ref(null)
const polygonGeoJSON = ref(null)
const savingSector = ref(false)
const sectorError = ref('')
const savedSectorIds = ref(new Set())

const approvingId = ref(null)
const approveError = ref('')

async function loadPending() {
    error.value = ''
    loading.value = true
    try {
        fields.value = await listPendingSectors()
    } catch (err) {
        error.value = 'No se pudieron cargar los sectores. Intente nuevamente.'
    } finally {
        loading.value = false
    }
}

function pendingSectors(field) {
  return (field.sectors || []).filter(s => s.status === 'pending')
}

function openSectorEditor(sector) {
    editingSector.value = sector
    polygonGeoJSON.value = sector.polygon_geojson || null
    sectorError.value = ''
}

function closeSectorEditor() {
    editingSector.value = null
}

async function saveSectorPolygon() {
    if (!editingSector.value || !polygonGeoJSON.value) return
    savingSector.value = true
    sectorError.value = ''
    try {
        const updated = await adminUpdateSector(editingSector.value.id, {
            polygon_geojson: polygonGeoJSON.value,
        })

        for (const f of fields.value) {
            const idx = (f.sectors || []).findIndex(s => s.id === updated.id)
            if (idx !== -1) f.sectors[idx] = updated
        }
        savedSectorIds.value.add(updated.id)
        closeSectorEditor()
    } catch (err) {
        sectorError.value = err.response?.data?.detail || 'No se pudo guardar el poligono'
    } finally {
        savingSector.value = false
    }
}

async function confirmApproval(sector) {
    approvingId.value = sector.id
    approveError.value = ''
    try {
        const updated = await approveSector(sector.id)
        for (const f of fields.value) {
          const idx = (f.sectors || []).findIndex(s => s.id === updated.id)
          if (idx !== -1) f.sectors[idx] = updated
        }
        // Si el campo ya no tiene sectores pendientes, lo saca de la lista
        fields.value = fields.value.filter(f => pendingSectors(f).length > 0)
    } catch (err) {
        approveError.value = err.response?.data?.detail || err.message || 'Error al aprobar el sector'
    } finally {
        approvingId.value = null
    }
}

onMounted(loadPending)
</script>

<template>
    <div class="max-w-2xl lg:max-w-5xl mx-auto px-4 py-6">

      <div class="flex items-center justify-between mb-5">
        <h1 class="text-xl font-bold text-gray-900">Sectores pendientes</h1>
        <button
          @click="loadPending"
          class="flex items-center gap-1.5 border-2 border-gray-200 text-gray-600 font-semibold text-sm px-3 py-2rounded-xl hover:border-gray-300 transition-colors"
        >
          <RefreshCw class="w-3.5 h-3.5" />
          Recargar
        </button>
      </div>

      <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">Cargando...</div>
      <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5rounded-xl">
        {{ error }}</div>
      <div v-else-if="fields.length === 0" class="text-center py-12 text-gray-400 text-sm">No hay sectores pendientes.</div>

      <div v-else class="space-y-4">
        <div
          v-for="field in fields"
          :key="field.id"
          class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden"
        >
          <div class="bg-amber-400 px-4 py-2">
            <span class="text-xs font-bold uppercase tracking-wide text-amber-900">
              {{ pendingSectors(field).length }} sector{{ pendingSectors(field).length === 1 ? '' : 'es' }} por aprobar
            </span>
          </div>

          <div class="p-4">
            <h2 class="text-base font-bold text-gray-900 mb-0.5">{{ field.name }}</h2>
            <p class="text-xs text-gray-400 mb-3">
              {{ field.user.name }} · {{ field.user.email }}
            </p>

            <div class="space-y-2">
              <div
                v-for="s in field.sectors" :key="s.id"
                class="border border-gray-200 rounded-xl px-3 py-2.5"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0">
                    <div class="text-sm font-semibold text-gray-800 truncate">{{ s.name }}</div>
                    <div class="text-xs text-gray-400">
                      {{ CROP_LABELS[s.crop_type] || s.crop_type }}<template v-if="s.variety"> · {{ s.variety}}</template> ·
                      {{ s.area_ha != null ? `${s.area_ha.toFixed(2)} ha` : 'sin área' }}
                    </div>
                  </div>
                  <div class="shrink-0">
                    <span
                      v-if="s.status === 'active'"
                      class="flex items-center gap-1 text-xs font-semibold text-green-700 px-2.5 py-1.5 rounded-lg border border-green-700 bg-green-50 cursor-default"
                    >
                      <Check class="w-3.5 h-3.5" />
                      Aprobado
                    </span>
                    <span
                      v-else-if="savedSectorIds.has(s.id)"
                      class="flex items-center gap-1 text-xs font-semibold text-green-700 px-2.5 py-1.5 rounded-lg border border-green-700 bg-green-50 cursor-default"
                    >
                      <MapPin class="w-3.5 h-3.5" />
                      Guardado
                    </span>
                    <button
                      v-else
                      @click="openSectorEditor(s)"
                      class="flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg transition-colors"
                      :class="s.polygon_geojson
                        ? 'text-green-800 border border-green-700 hover:bg-green-50'
                        : 'text-amber-700 border border-amber-400 hover:bg-amber-50'"
                    >
                      <MapPin class="w-3.5 h-3.5" />
                      {{ s.polygon_geojson ? 'Editar polígono' : 'Dibujar polígono' }}
                    </button>
                  </div>
                </div>

                <div v-if="s.status === 'pending'" class="mt-2.5">
                  <div v-if="approveError && approvingId === s.id" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2 rounded-lg mb-2">
                    {{ approveError }}
                  </div>
                  <button
                    @click="confirmApproval(s)"
                    :disabled="!s.polygon_geojson || approvingId === s.id"
                    class="w-full bg-green-800 hover:bg-green-700 text-white font-bold py-2 rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {{ approvingId === s.id ? 'Aprobando...' : 'Aprobar sector' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal editor de polígono de sector -->
      <div v-if="editingSector" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="closeSectorEditor">
        <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto flex flex-col">
          <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 class="text-base font-bold text-gray-900">Polígono de "{{ editingSector.name }}"</h2>
            <button @click="closeSectorEditor" class="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
          </div>

          <div class="p-4 flex-1 space-y-3">
            <p class="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5">
              Corregí el perímetro del sector si el productor lo dibujó mal (caminos, zonas fuera del cuadro, etc.).
            </p>
            <FieldMapEditor v-model="polygonGeoJSON" height="380px" />
            <div v-if="sectorError" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">
              {{ sectorError }}
            </div>
          </div>

          <div class="flex gap-3 px-5 py-4 border-t border-gray-100">
            <button
              @click="closeSectorEditor" :disabled="savingSector"
              class="flex-1 border-2 border-gray-200 text-gray-600 font-bold py-3 rounded-xl text-sm hover:border-gray-300 transition-colors disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              @click="saveSectorPolygon" :disabled="!polygonGeoJSON || savingSector"
              class="flex-1 bg-green-800 hover:bg-green-700 text-white font-bold py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ savingSector ? 'Guardando...' : 'Guardar polígono' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </template>
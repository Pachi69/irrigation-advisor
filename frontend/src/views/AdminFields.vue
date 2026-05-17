<script setup> 
import { ref, onMounted } from 'vue'
import { listPendingFields, approveField } from '../services/admin'
import FieldMapEditor from '../components/FieldMapEditor.vue'
import { RefreshCw } from 'lucide-vue-next'
import { CROP_LABELS, SOIL_LABELS, IRRIGATION_LABELS } from '../utils/labels'


const fields = ref([])
const loading = ref(true)
const error = ref('')

const approvingField = ref(null)
const polygonGeoJSON = ref(null)
const approving = ref(false)
const approveError = ref('')

async function loadPending() {
    error.value = ''
    loading.value = true
    try {
        fields.value = await listPendingFields()
    } catch (err) {
        error.value = 'No se pudieron cargar los campos. Intente nuevamente.'
    } finally {
        loading.value = false
    }
}

function openApproveModal(field) {
    approvingField.value = field
    polygonGeoJSON.value = field.polygon_geojson || null
    approveError.value = ''
}

function closeApproveModal() {
    approvingField.value = null
}

async function confirmApproval() {
    if (!approvingField.value || !polygonGeoJSON.value) return
    approving.value = true
    approveError.value = ''
    try {
        await approveField(approvingField.value.id, polygonGeoJSON.value)
        // Sacamos el campo aprobado de la lista de pendientes
        fields.value = fields.value.filter(f => f.id !== approvingField.value.id)
        closeApproveModal()
    } catch (err) {
        approveError.value = err.response?.data?.detail || err.message || 'Error al aprobar el campo'
    } finally {
        approving.value = false
    }
}

onMounted(loadPending)
</script>

<template>
    <div class="max-w-2xl lg:max-w-5xl mx-auto px-4 py-6">

        <div class="flex items-center justify-between mb-5">
            <h1 class="text-xl font-bold text-gray-900">Campos pendientes</h1>
            <button
                @click="loadPending"
                class="flex items-center gap-1.5 border-2 border-gray-200 text-gray-600 font-semibold text-sm px-3 py-2 rounded-xl hover:border-gray-300 transition-colors"
            >
                <RefreshCw class="w-3.5 h-3.5" />
                Recargar
            </button>
        </div>

        <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">Cargando...</div>
        <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>
        <div v-else-if="fields.length === 0" class="text-center py-12 text-gray-400 text-sm">No hay campos pendientes.</div>

        <div v-else class="space-y-4">
            <div
                v-for="field in fields"
                :key="field.id"
                class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden"
            >
                <div class="bg-amber-400 px-4 py-2">
                    <span class="text-xs font-bold uppercase tracking-wide text-amber-900">Pendiente de aprobación</span>
                </div>

                <div class="p-4">
                    <h2 class="text-base font-bold text-gray-900 mb-0.5">{{ field.name }}</h2>
                    <p class="text-xs text-gray-400 mb-3">
                        {{ field.user.name }} · {{ field.user.email }}
                    </p>

                    <div class="grid grid-cols-2 gap-x-4 gap-y-2.5 mb-4">
                        <div>
                            <p class="text-xs text-gray-400">Cultivo</p>
                            <p class="text-sm font-semibold text-gray-800">{{ CROP_LABELS[field.crop_type] }}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-400">Riego</p>
                            <p class="text-sm font-semibold text-gray-800">{{ IRRIGATION_LABELS[field.irrigation_type] }}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-400">Superficie</p>
                            <p class="text-sm font-semibold text-gray-800">
                                {{ field.area_ha != null ? `${field.area_ha.toFixed(2)} ha` : '—' }}
                            </p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-400">Siembra / brotación</p>
                            <p class="text-sm font-semibold text-gray-800">{{ field.planting_date }}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-400">Malla antigranizo</p>
                            <p class="text-sm font-semibold text-gray-800">{{ field.has_hail_net ? 'Sí' : 'No' }}</p>
                        </div>
                    </div>

                    <button
                        @click="openApproveModal(field)"
                        class="w-full bg-green-800 hover:bg-green-700 text-white font-bold py-2.5 rounded-xl text-sm transition-colors"
                    >
                        Aprobar campo
                    </button>
                </div>
            </div>
        </div>

        <!-- Modal de aprobación -->
        <div v-if="approvingField" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="closeApproveModal">
            <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto flex flex-col">

                <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                    <h2 class="text-base font-bold text-gray-900">Aprobar "{{ approvingField.name }}"</h2>
                    <button @click="closeApproveModal" class="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
                </div>

                <div class="p-4 flex-1 space-y-3">
                    <p class="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5">
                        Dibujá el perímetro del campo usando el ícono de polígono en el panel izquierdo del mapa.
                    </p>
                    <FieldMapEditor v-model="polygonGeoJSON" height="380px" />
                    <div v-if="approveError" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">
                        {{ approveError }}
                    </div>
                </div>

                <div class="flex gap-3 px-5 py-4 border-t border-gray-100">
                    <button
                        @click="closeApproveModal" :disabled="approving"
                        class="flex-1 border-2 border-gray-200 text-gray-600 font-bold py-3 rounded-xl text-sm hover:border-gray-300 transition-colors disabled:opacity-50"
                    >
                        Cancelar
                    </button>
                    <button
                        @click="confirmApproval" :disabled="!polygonGeoJSON || approving"
                        class="flex-1 bg-green-800 hover:bg-green-700 text-white font-bold py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {{ approving ? 'Aprobando...' : 'Confirmar aprobación' }}
                    </button>
                </div>

            </div>
        </div>

    </div>
</template>
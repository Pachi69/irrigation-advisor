<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createSector } from '../services/sectors'
import { useSectorForm } from '../composables/useSectorForm'
import SectorFormFields from '../components/sector/SectorFormFields.vue'
import FieldMapEditor from '../components/FieldMapEditor.vue'
import { MapPin } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const fieldId = route.params.id
const { normalizePayload } = useSectorForm()

const form = ref({
    name: '',
    crop_type: 'vine',
    variety: '',
    irrigation_type: 'aspersion',
    flow_rate_ls_ha: null,
    hail_net_type: 'none',
    notification_hour: '08:00:00',
    notification_frequency_days: 1,
    last_saturation_date: new Date().toISOString().slice(0, 10),
    polygon_geojson: null,
})

const loading = ref(false)
const error = ref('')
const showMapModal = ref(false)

async function handleSubmit() {
    error.value = ''
    if (!form.value.polygon_geojson) {
        error.value = 'Dibujá la ubicación del sector en el mapa.'
        return
    }
    loading.value = true
    try {
        await createSector(fieldId, normalizePayload(form.value))
        router.push(`/fields/${fieldId}`)
    } catch (err) {
        if (err.response?.status === 422) {
            error.value = 'Datos inválidos. Revisá el formulario.'
        } else {
            error.value = 'Error al crear el sector. Intentá nuevamente.'
        }
    } finally {
        loading.value = false
    }
}

function cancel() {
    router.push(`/fields/${fieldId}`)
}
</script>

<template>
    <div class="max-w-2xl mx-auto px-4 py-6">
        <h1 class="text-xl font-bold text-gray-900 mb-1">Nuevo sector</h1>
        <p class="text-sm text-gray-500 mb-5">
            Un sector agrupa una variedad con su propio riego y ubicación.
        </p>

        <form @submit.prevent="handleSubmit" class="space-y-4">

            <SectorFormFields
                :form="form"
                :disabled="loading"
                :saturation-required="true"
                saturation-help="Última fecha en que el suelo quedó bien empapado."
            >
                <template #crop>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-1.5">Cultivo</label>
                        <select v-model="form.crop_type" required :disabled="loading"
                            class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 bg-white transition-colors">
                            <option value="vine">Vid</option>
                            <option value="peach">Durazno</option>
                        </select>
                    </div>
                </template>

                <template #map>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-1.5">Ubicación del sector</label>
                        <button type="button" @click="showMapModal = true"
                            class="w-full flex items-center justify-between border-2 border-dashed border-gray-300 hover:border-green-600 rounded-xl px-4 py-3 transition-colors bg-white">
                            <div class="flex items-center gap-2">
                                <MapPin class="w-4 h-4 text-gray-400" />
                                <span class="text-sm font-medium text-gray-600">Abrir mapa y marcar sector</span>
                            </div>
                            <span v-if="form.polygon_geojson" class="text-xs font-bold text-green-700">Marcado</span>
                            <span v-else class="text-xs text-gray-400">Sin marcar</span>
                        </button>
                    </div>
                </template>
            </SectorFormFields>

            <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">
                {{ error }}
            </div>

            <div class="flex gap-3 pt-1">
                <button type="button" @click="cancel" :disabled="loading"
                    class="flex-1 border-2 border-gray-200 text-gray-600 font-bold py-3 rounded-xl text-sm hover:border-gray-300 transition-colors disabled:opacity-50">
                    Cancelar
                </button>
                <button type="submit" :disabled="loading"
                    class="flex-1 bg-green-800 hover:bg-green-700 text-white font-bold py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                    {{ loading ? 'Guardando...' : 'Crear sector' }}
                </button>
            </div>
        </form>

        <!-- Modal mapa -->
        <div v-if="showMapModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="showMapModal = false">
            <div class="bg-white rounded-2xl w-full max-w-3xl max-h-[92vh] overflow-y-auto flex flex-col">
                <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                    <h2 class="text-base font-bold text-gray-900">Marcá el perímetro del sector</h2>
                    <button @click="showMapModal = false" class="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
                </div>
                <p class="text-xs text-gray-500 px-5 py-3 bg-gray-50 border-b border-gray-100">
                    Tocá el ícono de polígono en el panel izquierdo, hacé clic en cada esquina y cerrá el contorno al final.
                </p>
                <div class="p-4 flex-1">
                    <FieldMapEditor v-model="form.polygon_geojson" height="500px" />
                </div>
                <div class="px-5 py-4 border-t border-gray-100 flex justify-end">
                    <button type="button" :disabled="!form.polygon_geojson" @click="showMapModal = false"
                        class="bg-green-800 hover:bg-green-700 text-white font-bold px-6 py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                        {{ form.polygon_geojson ? 'Confirmar ubicación' : 'Dibujá el sector primero' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSectorById, updateSector, deleteSector } from '../services/sectors'
import { useSectorForm } from '../composables/useSectorForm'
import SectorFormFields from '../components/sector/SectorFormFields.vue'

const route = useRoute()
const router = useRouter()
const { normalizePayload } = useSectorForm()

const form = ref(null)
const fieldId = ref(null)
const loading = ref(true)
const error = ref('')
const saving = ref(false)
const showDeleteModal = ref(false)
const deleting = ref(false)
const deleteError = ref('')

onMounted(async () => {
    try {
        const sector = await getSectorById(route.params.id)
        fieldId.value = sector.field_id
        form.value = {
            name: sector.name,
            variety: sector.variety || '',
            irrigation_type: sector.irrigation_type,
            flow_rate_ls_ha: sector.flow_rate_ls_ha,
            hail_net_type: sector.hail_net_type,
            notification_hour: sector.notification_hour || '08:00:00',
            notification_frequency_days: sector.notification_frequency_days || 1,
            last_saturation_date: sector.last_saturation_date,
        }
    } catch {
        error.value = 'No se pudo cargar el sector'
    } finally {
        loading.value = false
    }
})

function backToField() {
    router.push(fieldId.value ? `/fields/${fieldId.value}` : '/fields')
}

async function handleSubmit() {
    saving.value = true
    error.value = ''
    try {
        await updateSector(route.params.id, normalizePayload(form.value))
        backToField()
    } catch {
        error.value = 'No se pudo guardar los cambios. Intentá nuevamente.'
    } finally {
        saving.value = false
    }
}

async function confirmDelete() {
    deleting.value = true
    deleteError.value = ''
    try {
        await deleteSector(route.params.id)
        backToField()
    } catch {
        deleteError.value = 'No se pudo eliminar el sector. Intentá nuevamente.'
        deleting.value = false
    }
}
</script>

<template>
    <div class="max-w-2xl mx-auto px-4 py-6">
        <h1 class="text-xl font-bold text-gray-900 mb-5">Editar sector</h1>

        <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">Cargando...</div>
        <div v-else-if="error && !form" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">
            {{ error }}
        </div>

        <form v-else-if="form" @submit.prevent="handleSubmit" class="space-y-4">

            <SectorFormFields :form="form" :disabled="saving" />

            <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">
                {{ error }}
            </div>

            <div class="flex gap-3 pt-1">
                <button type="button" @click="backToField" :disabled="saving"
                    class="flex-1 border-2 border-gray-200 text-gray-600 font-bold py-3 rounded-xl text-sm hover:border-gray-300 transition-colors disabled:opacity-50">
                    Cancelar
                </button>
                <button type="submit" :disabled="saving"
                    class="flex-1 bg-green-800 hover:bg-green-700 text-white font-bold py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                    {{ saving ? 'Guardando...' : 'Guardar cambios' }}
                </button>
            </div>

            <div class="pt-3 mt-3 border-t border-gray-200">
                <button type="button" @click="deleteError = ''; showDeleteModal = true" :disabled="saving"
                    class="text-sm font-semibold text-red-600 hover:text-red-700 transition-colors disabled:opacity-50">
                    Eliminar este sector
                </button>
            </div>
        </form>

        <div v-if="showDeleteModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="showDeleteModal = false">
            <div class="bg-white rounded-2xl w-full max-w-sm flex flex-col">
                <div class="px-5 py-4 border-b border-gray-100">
                    <h2 class="text-base font-bold text-gray-900">Eliminar sector</h2>
                </div>
                <div class="px-5 py-4 text-sm text-gray-700 leading-relaxed">
                    ¿Seguro que querés eliminar <strong>{{ form.name }}</strong>? Se borrarán también su historial de recomendaciones y datos asociados. Esta acción no se puede deshacer.
                    <div v-if="deleteError" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl mt-3">
                        {{ deleteError }}
                    </div>
                </div>
                <div class="px-5 py-4 border-t border-gray-100 flex gap-3 justify-end">
                    <button type="button" @click="showDeleteModal = false" :disabled="deleting"
                        class="border-2 border-gray-200 text-gray-600 font-bold py-2.5 px-4 rounded-xl text-sm hover:border-gray-300 transition-colors disabled:opacity-50">
                        Cancelar
                    </button>
                    <button type="button" @click="confirmDelete" :disabled="deleting"
                        class="bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 px-5 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                        {{ deleting ? 'Eliminando...' : 'Eliminar' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSectorById, updateSector, deleteSector } from '../services/sectors'

const route = useRoute()
const router = useRouter()

const form = ref(null)
const fieldId = ref(null)
const loading = ref(true)
const error = ref('')
const saving = ref(false)
const showDeleteModal = ref(false)
const deleting = ref(false)
const deleteError = ref('')

const todayStr = new Date().toISOString().slice(0, 10)

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
        await updateSector(route.params.id, {
            ...form.value,
            variety: form.value.variety || null,
        })
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
        <div v-else-if="error && !form" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>

        <form v-else-if="form" @submit.prevent="handleSubmit" class="space-y-4">

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre del sector</label>
                <input
                    v-model="form.name"
                    type="text" required minlength="2" maxlength="255" :disabled="saving"
                    class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
                />
            </div>

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Variedad</label>
                <input
                    v-model="form.variety"
                    type="text" maxlength="255" :disabled="saving"
                    placeholder="Ej: Malbec"
                    class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
                />
            </div>

            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1.5">Tipo de riego</label>
                    <select
                        v-model="form.irrigation_type" required :disabled="saving"
                        class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 bg-white transition-colors"
                    >
                        <option value="aspersion">Aspersión</option>
                        <option value="superficial">Superficial</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1.5">Malla antigranizo</label>
                    <select
                        v-model="form.hail_net_type" required :disabled="saving"
                        class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 bg-white transition-colors"
                    >
                        <option value="none">Sin malla</option>
                        <option value="open">Malla abierta</option>
                        <option value="dense">Malla densa</option>
                        <option value="color">Malla de color</option>
                    </select>
                </div>
            </div>

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Caudal (L/s/ha)</label>
                <input
                    v-model.number="form.flow_rate_ls_ha"
                    type="number" min="0.1" step="0.1" :disabled="saving"
                    class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 transition-colors"
                />
            </div>

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Último riego completo o lluvia abundante</label>
                <input
                    v-model="form.last_saturation_date"
                    type="date" :max="todayStr" :disabled="saving"
                    class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
                />
                <p class="text-xs text-gray-400 mt-1.5">Actualizá esta fecha tras un riego completo para recalibrar el balance hídrico.</p>
            </div>

            <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">
                {{ error }}
            </div>

            <div class="flex gap-3 pt-1">
                <button
                    type="button" @click="backToField" :disabled="saving"
                    class="flex-1 border-2 border-gray-200 text-gray-600 font-bold py-3 rounded-xl text-sm hover:border-gray-300 transition-colors disabled:opacity-50"
                >
                    Cancelar
                </button>
                <button
                    type="submit" :disabled="saving"
                    class="flex-1 bg-green-800 hover:bg-green-700 text-white font-bold py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {{ saving ? 'Guardando...' : 'Guardar cambios' }}
                </button>
            </div>

            <div class="pt-3 mt-3 border-t border-gray-200">
                <button
                    type="button" @click="deleteError = ''; showDeleteModal = true" :disabled="saving"
                    class="text-sm font-semibold text-red-600 hover:text-red-700 transition-colors disabled:opacity-50"
                >
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
                    <button
                        type="button" @click="showDeleteModal = false" :disabled="deleting"
                        class="border-2 border-gray-200 text-gray-600 font-bold py-2.5 px-4 rounded-xl text-sm hover:border-gray-300 transition-colors disabled:opacity-50"
                    >
                        Cancelar
                    </button>
                    <button
                        type="button" @click="confirmDelete" :disabled="deleting"
                        class="bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 px-5 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {{ deleting ? 'Eliminando...' : 'Eliminar' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
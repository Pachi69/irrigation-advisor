<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getFieldById, updateField, deleteField } from '../services/fields'

const route = useRoute()
const router = useRouter()

const form = ref(null)
const loading = ref(true)
const error = ref('')
const saving = ref(false)
const showDeleteModal = ref(false)
const deleting = ref(false)
const deleteError = ref('')


onMounted(async () => {
    try {
        const field = await getFieldById(route.params.id)
        form.value = {
            name: field.name,
        }
    } catch {
        error.value = 'No se pudo cargar el campo'
    } finally {
        loading.value = false
    }
})

function backToField() {
    router.push(`/fields/${route.params.id}`)
}

async function handleSubmit() {
    saving.value = true
    error.value = ''
    try {
        await updateField(route.params.id, {
            ...form.value,
        })
        backToField()
    } catch {
        error.value = 'No se pudo guardar los cambios, Intenta nuevamente'
    } finally {
        saving.value = false
    }
}

async function confirmDelete() {
    deleting.value = true
    deleteError.value = ''
    try {
        await deleteField(route.params.id)
        router.push('/fields')
    } catch {
        deleteError.value = 'No se pudo eliminar el campo, Intenta nuevamente'
        deleting.value = false
    }
}

</script>

<template>
    <div class="max-w-2xl mx-auto px-4 py-6">
        <h1 class="text-xl font-bold text-gray-900 mb-5">Editar campo</h1>

        <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">Cargando...</div>
        <div v-else-if="error && !form" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>

        <form v-else-if="form" @submit.prevent="handleSubmit" class="space-y-4">

        <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre del campo</label>
            <input
                v-model="form.name"
                type="text" required minlength="2" maxlength="255" :disabled="saving"
                class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
            />
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
                Eliminar mi campo
            </button>
        </div>

        </form>

        <div v-if="showDeleteModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="showDeleteModal = false">
            <div class="bg-white rounded-2xl w-full max-w-sm flex flex-col">
                <div class="px-5 py-4 border-b border-gray-100">
                    <h2 class="text-base font-bold text-gray-900">Eliminar campo</h2>
                </div>
                <div class="px-5 py-4 text-sm text-gray-700 leading-relaxed">
                    ¿Seguro que querés eliminar <strong>{{ form.name }}</strong>? Se borrarán también sus sectores, historial de recomendaciones y datos asociados. Esta acción no se puede deshacer.
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
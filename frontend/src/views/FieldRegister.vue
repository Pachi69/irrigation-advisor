<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createField } from '../services/fields'

const router = useRouter()

const form = ref({
    name: '',
})

const loading = ref(false)
const error = ref('')


async function handleSubmit() {
    error.value = ''
    loading.value = true
    try {
        const field = await createField({ ...form.value })
        // Tras crear el campo va al detalle para agregar sectores
        router.push(`/fields/${field.id}`)
    } catch (err) {
        if (err.response?.status === 409) {
            error.value = 'Ya tenes un campo pendiente de aprobacion'
        } else if (err.response?.status === 422) {
            error.value = 'Datos inválidos. Revisá el formulario.'
        } else {
            error.value = 'Error al registrar el campo. Intentá nuevamente.'
        }
    } finally {
        loading.value = false
    }
}

function cancel() {
    router.push('/fields')
}
</script>

<template>
    <div class="max-w-2xl mx-auto px-4 py-6">
        <h1 class="text-xl font-bold text-gray-900 mb-1">Registrar nuevo campo</h1>
        <p class="text-sm text-blue-700 bg-blue-50 border border-blue-200 rounded-xl px-3 py-2.5 mb-5">
            Primero creá el campo. Después vas a poder agregar uno o más sectores con su variedad y ubicación.
        </p>

        <form @submit.prevent="handleSubmit" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre del campo</label>
                <input
                    v-model="form.name"
                    type="text" required minlength="2" maxlength="255"
                    placeholder="Ej: Finca Los Álamos"
                    :disabled="loading"
                    class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
                />
            </div>

            <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">
                {{ error }}
            </div>

            <div class="flex gap-3 pt-1">
                <button
                    type="button" @click="cancel" :disabled="loading"
                    class="flex-1 border-2 border-gray-200 text-gray-600 font-bold py-3 rounded-xl text-sm hover:border-gray-300 transition-colors disabled:opacity-50"
                >
                    Cancelar
                </button>
                <button
                    type="submit" :disabled="loading"
                    class="flex-1 bg-green-800 hover:bg-green-700 text-white font-bold py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {{ loading ? 'Guardando...' : 'Crear campo' }}
                </button>
            </div>
        </form>
    </div>
</template>
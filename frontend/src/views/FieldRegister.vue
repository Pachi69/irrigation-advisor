<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createField } from '../services/fields'
import FieldMapEditor from '../components/FieldMapEditor.vue'
import { MapPin } from 'lucide-vue-next'


const router = useRouter()

const form = ref({
    name: '',
    crop_type: 'vine',
    irrigation_type: 'drip',
    has_hail_net: false,
    planting_date: '',
    last_saturation_date: new Date().toISOString().slice(0, 10),
    polygon_geojson: null,
})

const loading = ref(false)
const error = ref('')
const showMapModal = ref(false)
const showSaturationTip = ref(true)
const saturationTipAccepted = ref(false)

async function handleSubmit() {
    error.value = ''
    loading.value = true
    try {
        await createField({
            ...form.value,
        })
        router.push('/fields')
    } catch (err) {
        if (err.response?.status === 422) {
            error.value = 'Datos invalidos. Revisa el formulario.'
        } else {
            error.value = 'Error al registrar el campo. Intenta nuevamente.'
        }
    } finally {
        loading.value = false
    }
}

function cancel() {
    router.push('/fields')
}

const todayStr = new Date().toISOString().slice(0, 10)
</script>

<template>
    <div class="max-w-2xl mx-auto px-4 py-6">
        <h1 class="text-xl font-bold text-gray-900 mb-1">Registrar nuevo campo</h1>
        <p class="text-sm text-blue-700 bg-blue-50 border border-blue-200 rounded-xl px-3 py-2.5 mb-5">
            Dibujá el perímetro de tu campo en el mapa para agilizar la aprobación.
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

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Cultivo</label>
                <select
                    v-model="form.crop_type" required :disabled="loading"
                    class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 bg-white transition-colors"
                >
                    <option value="vine">Vid</option>
                    <option value="peach">Durazno</option>
                    <option value="alfalfa">Alfalfa</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Tipo de riego</label>
                <select
                    v-model="form.irrigation_type" required :disabled="loading"
                    class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 bg-white transition-colors"
                >
                    <option value="drip">Goteo</option>
                    <option value="sprinkler">Aspersión</option>
                    <option value="flood">Surco</option>
                </select>
            </div>

            <!-- Mapa -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Ubicación del campo</label>
                <button
                    type="button"
                    @click="showMapModal = true"
                    class="w-full flex items-center justify-between border-2 border-dashed border-gray-300 hover:border-green-600 rounded-xl px-4 py-3 transition-colors bg-white"
                >
                    <div class="flex items-center gap-2">
                        <MapPin class="w-4 h-4 text-gray-400" />
                        <span class="text-sm font-medium text-gray-600">Abrir mapa y marcar campo</span>
                    </div>
                    <span v-if="form.polygon_geojson" class="text-xs font-bold text-green-700">Marcado ✓</span>
                    <span v-else class="text-xs text-gray-400">Sin marcar</span>
                </button>
            </div>

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Fecha de siembra o brotación</label>
                <input
                    v-model="form.planting_date"
                    type="date" required :disabled="loading"
                    class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
                />
            </div>

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Último riego completo o lluvia abundante</label>
                <input
                    v-model="form.last_saturation_date"
                    type="date" :max="todayStr" required :disabled="loading"
                    class="w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 disabled:bg-gray-50 transition-colors"
                />
                <p class="text-xs text-gray-400 mt-1.5">Última fecha en que el suelo quedó bien empapado.</p>
            </div>

            <label class="flex items-center gap-3 bg-white border-2 border-gray-200 rounded-xl px-4 py-3 cursor-pointer hover:border-gray-300 transition-colors">
                <input
                    v-model="form.has_hail_net"
                    type="checkbox" :disabled="loading"
                    class="w-4 h-4 accent-green-700"
                />
                <span class="text-sm font-semibold text-gray-700">El campo tiene malla antigranizo</span>
            </label>

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
                    {{ loading ? 'Guardando...' : 'Registrar campo' }}
                </button>
            </div>

        </form>

        <!-- Modal mapa -->
        <div v-if="showMapModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="showMapModal = false">
            <div class="bg-white rounded-2xl w-full max-w-3xl max-h-[92vh] overflow-y-auto flex flex-col">
                <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                    <h2 class="text-base font-bold text-gray-900">Marcá el perímetro de tu campo</h2>
                    <button @click="showMapModal = false" class="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
                </div>
                <p class="text-xs text-gray-500 px-5 py-3 bg-gray-50 border-b border-gray-100">
                    Tocá el ícono de polígono en el panel izquierdo, hacé clic en cada esquina y cerrá el contorno al final.
                </p>
                <div class="p-4 flex-1">
                    <FieldMapEditor v-model="form.polygon_geojson" height="500px" />
                </div>
                <div class="px-5 py-4 border-t border-gray-100 flex justify-end">
                    <button
                        type="button"
                        :disabled="!form.polygon_geojson"
                        @click="showMapModal = false"
                        class="bg-green-800 hover:bg-green-700 text-white font-bold px-6 py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {{ form.polygon_geojson ? 'Confirmar ubicación' : 'Dibujá el campo primero' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Modal tip saturación -->
        <div v-if="showSaturationTip" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-2xl w-full max-w-sm flex flex-col">
                <div class="px-5 py-4 border-b border-gray-100">
                    <h2 class="text-base font-bold text-gray-900">Antes de registrar tu campo</h2>
                </div>
                <div class="px-5 py-4 text-sm text-gray-700 leading-relaxed">
                    <p>
                        Para una primera recomendación precisa,
                        <strong>regá el campo hoy o ayer hasta saturar el suelo</strong>
                        (que quede bien empapado). Luego indicá esa fecha en el formulario como "Último riego completo".
                    </p>
                    <label class="flex items-center gap-2.5 mt-4 cursor-pointer">
                        <input type="checkbox" v-model="saturationTipAccepted" class="w-4 h-4 accent-green-700" />
                        <span class="text-sm font-semibold text-gray-700">Entendido, lo haré antes de registrar</span>
                    </label>
                </div>
                <div class="px-5 py-4 border-t border-gray-100 flex justify-end">
                    <button
                        type="button"
                        :disabled="!saturationTipAccepted"
                        @click="showSaturationTip = false"
                        class="bg-green-800 hover:bg-green-700 text-white font-bold px-6 py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Continuar
                    </button>
                </div>
            </div>
        </div>

    </div>
</template>
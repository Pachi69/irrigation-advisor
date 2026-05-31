<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPendingConfirmations, confirmIrrigation } from '../services/sectors'
import { ArrowLeft, Droplet } from 'lucide-vue-next'
import { URGENCY_LABEL } from '../utils/labels'

const route = useRoute()
const router = useRouter()

const items = ref([])
const loading = ref(true)
const error = ref('')

const selected = ref(null)
const form = ref({ irrigation_date: '', applied_irrigation_mm: null })
const submitting = ref(false)
const formError = ref('')

const today = new Date().toISOString().slice(0, 10)

async function load() {
    loading.value = true
    error.value = ''
    try {
        items.value = await getPendingConfirmations(route.params.id)
    } catch {
        error.value = 'No se pudieron cargar las recomendaciones pendientes'
    } finally {
        loading.value = false
    }
}

function openConfirm(item) {
    selected.value = item
    form.value = {
        irrigation_date: item.date,
        applied_irrigation_mm: item.recommended_irrigation_mm
    }
    formError.value = ''
}

function closeConfirm() {
    selected.value = null
}

async function submit() {
    formError.value = ''
    const mm = Number(form.value.applied_irrigation_mm)
    if (!(mm > 0)) {
        formError.value = 'Ingresa una lamina mayor a 0 mm'
        return
    }
    if (!form.value.irrigation_date) {
        formError.value = 'Elegi la fecha de riego'
        return
    }
    if (form.value.irrigation_date > today) {
        formError.value = 'La fecha de riego no puede ser futura'
        return
    }
    submitting.value = true
    try {
        await confirmIrrigation(route.params.id, selected.value.recommendation_id, {
            irrigation_date: form.value.irrigation_date,
            applied_irrigation_mm: mm,
        })
        items.value = items.value.filter(
            (i) => i.recommendation_id !== selected.value.recommendation_id,
        )
        closeConfirm()
    } catch (e) {
        formError.value = e?.response?.data?.detail || 'No se pudo confirmar el riego'
    } finally {
        submitting.value = false
    }
}

onMounted(load)
</script>

<template>
    <div class="max-w-2xl lg:max-w-3xl mx-auto px-4 py-6">

        <div class="flex items-center justify-between mb-5">
            <button
                @click="router.push(`/sectors/${route.params.id}/recommendation`)"
                class="flex items-center gap-1 text-green-800 font-semibold text-sm hover:underline"
            >
                <ArrowLeft class="w-4 h-4" />
                Recomendación
            </button>
            <h1 class="text-base font-bold text-gray-900">Confirmar riego</h1>
            <span class="w-24"></span>
        </div>

        <p class="text-sm text-gray-500 mb-4">
            Confirmá cuánto y cuándo regaste para ajustar el balance hídrico.
        </p>

        <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">Cargando...</div>
        <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>
        <div v-else-if="items.length === 0" class="text-center py-12 text-gray-400 text-sm">No tenés riegos pendientes de confirmar.</div>

        <div v-else>
            <!-- Encabezado de columnas -->
            <div class="grid grid-cols-[6rem_1fr_7rem_1fr_auto] items-center gap-3 px-4 mb-1.5">
                <span class="app-label">Fecha</span>
                <span class="app-label">Urgencia</span>
                <span class="app-label justify-self-end">Recomendado</span>
                <span></span>
                <span aria-hidden="true" class="invisible flex items-center gap-1 text-sm font-semibold px-3 py-1.5">
                    <Droplet class="w-3.5 h-3.5" />
                    Confirmar
                </span>
            </div>

            <div class="space-y-2">
                <div
                    v-for="item in items"
                    :key="item.recommendation_id"
                    class="bg-white rounded-2xl border border-gray-200 shadow-sm px-4 py-3 grid grid-cols-[6rem_1fr_7rem_1fr_auto] items-center gap-3"
                >
                    <span class="text-sm text-gray-500">{{ item.date }}</span>

                    <span :class="[
                        'justify-self-start text-xs font-bold px-2.5 py-1 rounded-full',
                        item.urgency === 'low'    ? 'bg-green-100 text-green-800' :
                        item.urgency === 'medium' ? 'bg-amber-100 text-amber-800' :
                        item.urgency === 'high'   ? 'bg-orange-100 text-orange-800' :
                                                    'bg-red-100 text-red-700'
                    ]">
                        {{ URGENCY_LABEL[item.urgency] }}
                    </span>

                    <span class="justify-self-end text-sm font-bold text-gray-900">
                        {{ item.recommended_irrigation_mm }} mm
                    </span>

                    <span></span>

                    <button
                        @click="openConfirm(item)"
                        class="justify-self-end flex items-center gap-1 text-sm font-semibold text-white bg-green-800 hover:bg-green-700 px-3 py-1.5 rounded-xl transition-colors"
                    >
                        <Droplet class="w-3.5 h-3.5" />
                        Confirmar
                    </button>
                </div>
            </div>
        </div>

        <!-- Modal de confirmacion -->
        <div
            v-if="selected"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
            @click.self="closeConfirm"
        >
            <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-5">
                <h2 class="text-base font-bold text-gray-900 mb-1">Confirmar riego</h2>
                <p class="text-sm text-gray-500 mb-4">Recomendación del {{ selected.date }}</p>

                <label class="block text-sm font-semibold text-gray-700 mb-1">Fecha de riego</label>
                <input
                    type="date"
                    v-model="form.irrigation_date"
                    :max="today"
                    class="w-full border border-gray-300 rounded-xl px-3 py-2 mb-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-700"
                />

                <label class="block text-sm font-semibold text-gray-700 mb-1">Lámina aplicada (mm)</label>
                <input
                    type="number"
                    v-model="form.applied_irrigation_mm"
                    min="0"
                    step="0.1"
                    class="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-700"
                />

                <p v-if="formError" class="text-red-600 text-sm font-medium mt-3">{{ formError }}</p>

                <div class="flex gap-2 mt-5">
                    <button
                        @click="closeConfirm"
                        :disabled="submitting"
                        class="flex-1 text-sm font-semibold text-green-800 border-2 border-green-800 px-3 py-2 rounded-xl hover:bg-green-50 transition-colors disabled:opacity-50"
                    >
                        Cancelar
                    </button>
                    <button
                        @click="submit"
                        :disabled="submitting"
                        class="flex-1 text-sm font-semibold text-white bg-green-800 hover:bg-green-700 px-3 py-2 rounded-xl transition-colors disabled:opacity-50"
                    >
                        {{ submitting ? 'Confirmando...' : 'Confirmar' }}
                    </button>
                </div>
            </div>
        </div>

    </div>
</template>
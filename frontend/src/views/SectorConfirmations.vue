<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPendingConfirmations, confirmIrrigation, getSectorById } from '../services/sectors'
import { ArrowLeft, Droplet } from 'lucide-vue-next'
import { URGENCY_LABEL } from '../utils/labels'
import { formatMinutes } from '../utils/format'

const route = useRoute()
const router = useRouter()

const items = ref([])
const sector = ref(null)
const loading = ref(true)
const error = ref('')

const selected = ref(null)
const form = ref({ irrigation_date: '', hours: 0, minutes: 0, volume_m3: null })
const submitting = ref(false)
const formError = ref('')

const today = new Date().toISOString().slice(0, 10)

const hasCaudal = computed(() => sector.value?.flow_rate_ls_ha != null)

async function load() {
    loading.value = true
    error.value = ''
    try {
        [items.value, sector.value] = await Promise.all([
            getPendingConfirmations(route.params.id),
            getSectorById(route.params.id),
        ])
    } catch {
        error.value = 'No se pudieron cargar las recomendaciones pendientes'
    } finally {
        loading.value = false
    }
}

function openConfirm(item) {
    selected.value = item
    // Precarga el tiempo recomendado (item.time_min) partido en horas y minutos
    const total = Math.round(item.time_min || 0)
    form.value = {
        irrigation_date: item.date,
        hours: Math.floor(total / 60),
        minutes: total % 60,
        volume_m3: null,
    }
    formError.value = ''
}

function closeConfirm() {
    selected.value = null
}

async function submit() {
    formError.value = ''
    if (!form.value.irrigation_date) {
        formError.value = 'Elegi la fecha de riego'
        return
    }
    if (form.value.irrigation_date > today) {
        formError.value = 'La fecha de riego no puede ser futura'
        return
    }

    const payload = { irrigation_date: form.value.irrigation_date }

    if (hasCaudal.value) {
        const totalMin = (Number(form.value.hours) || 0) * 60 + (Number(form.value.minutes) || 0)
        if (!(totalMin > 0)) {
            formError.value = 'Ingresa un tiempo de riego mayor a 0 min'
            return
        }
        payload.applied_time_min = totalMin
    } else {
        const vol = Number(form.value.volume_m3)
        if (!(vol > 0)) {
            formError.value = 'Ingresa un volumen de riego mayor a 0 m3'
            return
        }
        payload.applied_volume_m3 = vol
    }

    submitting.value = true
    try {
        await confirmIrrigation(route.params.id, selected.value.recommendation_id, payload)
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
            <div class="hidden md:grid grid-cols-[6rem_1fr_7rem_1fr_auto] items-center gap-3 px-4 mb-1.5">
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
                    class="bg-white rounded-2xl border border-gray-200 shadow-sm px-4 py-3 grid grid-cols-2 gap-x-3 gap-y-2.5 items-center
                    md:grid-cols-[6rem_1fr_7rem_1fr_auto] md:gap-3"
                >
                    <span class="justify-self-start order-1 md:order-none text-sm text-gray-500">{{ item.date }}</span>

                    <span :class="[
                        'justify-self-start order-3 md:order-none text-xs font-bold px-2.5 py-1 rounded-full',
                        item.urgency === 'low'    ? 'bg-green-100 text-green-800' :
                        item.urgency === 'medium' ? 'bg-amber-100 text-amber-800' :
                        item.urgency === 'high'   ? 'bg-orange-100 text-orange-800' :
                                                    'bg-red-100 text-red-700'
                    ]">
                        {{ URGENCY_LABEL[item.urgency] }}
                    </span>

                    <span class="justify-self-end order-2 md:order-none text-sm font-bold text-gray-900">
                        {{ hasCaudal ? formatMinutes(item.time_min) : `${item.recommended_irrigation_mm.toFixed(0)} mm` }}
                    </span>

                    <span class="hidden md:block"></span>

                    <button
                        @click="openConfirm(item)"
                        class="justify-self-end order-4 md:order-none flex items-center gap-1 text-sm font-semibold text-white bg-green-800 hover:bg-green-700 px-3 py-1.5 rounded-xl transition-colors"
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

                <!-- Por tiempo (si hay caudal) -->
                <template v-if="hasCaudal">
                    <label class="block text-sm font-semibold text-gray-700 mb-1">Tiempo de riego aplicado</label>
                    <div class="flex gap-2">
                        <div class="flex-1">
                            <input
                                type="number" v-model="form.hours" min="0" placeholder="0"
                                class="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-700"
                            />
                            <span class="block text-[11px] text-gray-400 mt-1 text-center">horas</span>
                        </div>
                        <div class="flex-1">
                            <input
                                type="number" v-model="form.minutes" min="0" max="59" placeholder="0"
                                class="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-700"
                            />
                            <span class="block text-[11px] text-gray-400 mt-1 text-center">minutos</span>
                        </div>
                    </div>
                </template>

                <!-- Por volumen (si no hay caudal) -->
                <template v-else>
                    <label class="block text-sm font-semibold text-gray-700 mb-1">Volumen de riego aplicado</label>
                    <div class="relative">
                        <input
                            type="number" v-model="form.volume_m3" min="0" step="any" placeholder="0"
                            class="w-full border border-gray-300 rounded-xl px-3 py-2 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-green-700"
                        />
                        <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-400">m³</span>
                    </div>
                    <p class="text-[11px] text-gray-400 mt-1">
                        Este sector no tiene caudal cargado, así que confirmá el agua aplicada en m³.
                    </p>
                </template>

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
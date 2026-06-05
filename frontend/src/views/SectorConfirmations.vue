<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPendingConfirmations, confirmIrrigation, getSectorById } from '../services/sectors'
import { ArrowLeft, Droplet } from 'lucide-vue-next'
import { URGENCY_LABEL } from '../utils/labels'
import { formatMinutes } from '../utils/format'

const URG = {
    none:     { bg: 'var(--color-primary-soft)', fg: 'var(--color-primary)',   dot: 'var(--color-primary)' },
    low:      { bg: 'var(--color-primary-soft)', fg: 'var(--color-primary)',   dot: 'var(--color-primary)' },
    medium:   { bg: 'var(--color-amber-soft)',   fg: 'var(--color-amber-ink)', dot: 'var(--color-amber)' },
    high:     { bg: '#F1D8C4',                    fg: '#8A3D12',                dot: '#D8651C' },
    critical: { bg: 'var(--color-rust-soft)',    fg: 'var(--color-rust)',      dot: 'var(--color-rust)' },
}
const urg = (u) => URG[u] || URG.none

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

const recLabel = computed(() => (hasCaudal.value ? 'Tiempo recomendado' : 'Volumen recomendado'))

function recValue(item) {
    if (hasCaudal.value) return formatMinutes(item.time_min)
    return item.volume_m3 != null ? `${Math.round(item.volume_m3)} m³` : '—'
}

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
    // Precarga el tiempo recomendado (partido en h/min) o el volumen recomendado en m³
    const total = Math.round(item.time_min || 0)
    form.value = {
        irrigation_date: item.date,
        hours: Math.floor(total / 60),
        minutes: total % 60,
        volume_m3: hasCaudal.value ? null : (item.volume_m3 != null ? Math.round(item.volume_m3) : null),
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
                class="flex items-center gap-1 text-primary font-semibold text-sm hover:underline"
            >
                <ArrowLeft class="w-4 h-4" />
                Recomendación
            </button>
            <h1 class="text-base font-bold text-ink">Confirmar riego</h1>
            <span class="w-24"></span>
        </div>

        <p class="text-sm text-muted mb-4">
            Confirmá cuánto y cuándo regaste para ajustar el balance hídrico.
        </p>

        <div v-if="loading" class="text-center py-12 text-soft text-sm">Cargando...</div>
        <div v-else-if="error" class="bg-rust-soft border border-rust/30 text-rust text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>
        <div v-else-if="items.length === 0" class="text-center py-12 text-soft text-sm">No tenés riegos pendientes de confirmar.</div>

        <div v-else>
            <!-- MOBILE -->
            <div class="md:hidden flex flex-col gap-3">
                <div
                    v-for="item in items"
                    :key="item.recommendation_id"
                    class="bg-surface rounded-3xl border border-line p-4"
                >
                    <div class="flex items-center justify-between mb-3.5">
                        <span class="text-sm font-bold text-ink">{{ item.date }}</span>
                        <span
                            class="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full"
                            :style="{ background: urg(item.urgency).bg, color: urg(item.urgency).fg }"
                        >
                            <span class="w-1.5 h-1.5 rounded-full" :style="{ background: urg(item.urgency).dot }"></span>
                            {{ URGENCY_LABEL[item.urgency] }}
                        </span>
                    </div>

                    <div class="flex items-center justify-between bg-paper rounded-2xl px-3.5 py-3 mb-3.5">
                        <span class="app-label">{{ recLabel }}</span>
                        <span class="app-mono text-xl font-bold text-ink">{{ recValue(item) }}</span>
                    </div>

                    <button
                        @click="openConfirm(item)"
                        class="w-full flex items-center justify-center gap-2 text-sm font-bold text-white bg-primary hover:bg-green-700 px-4 py-3 rounded-xl transition-colors"
                    >
                        <Droplet class="w-4 h-4" />
                        Confirmar riego
                    </button>
                </div>
            </div>

            <!-- DESKTOP -->
            <div class="hidden md:block">
                <!-- Encabezado de columnas -->
                <div class="grid grid-cols-[6rem_1fr_7rem_auto] items-center gap-3 px-4 mb-1.5">
                    <span class="app-label">Fecha</span>
                    <span class="app-label">Urgencia</span>
                    <span class="app-label justify-self-end">Recomendado</span>
                    <span aria-hidden="true" class="invisible flex items-center gap-1 text-sm font-semibold px-3 py-1.5">
                        <Droplet class="w-3.5 h-3.5" />
                        Confirmar
                    </span>
                </div>

                <div class="space-y-2">
                    <div
                        v-for="item in items"
                        :key="item.recommendation_id"
                        class="bg-surface rounded-2xl border border-line shadow-sm px-4 py-3 grid grid-cols-[6rem_1fr_7rem_auto] gap-3 items-center"
                    >
                        <span class="text-sm text-muted">{{ item.date }}</span>

                        <span
                            class="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full justify-self-start"
                            :style="{ background: urg(item.urgency).bg, color: urg(item.urgency).fg }"
                        >
                            <span class="w-1.5 h-1.5 rounded-full" :style="{ background: urg(item.urgency).dot }"></span>
                            {{ URGENCY_LABEL[item.urgency] }}
                        </span>

                        <span class="text-sm font-bold text-ink justify-self-end">
                            {{ recValue(item) }}
                        </span>

                        <button
                            @click="openConfirm(item)"
                            class="flex items-center gap-1 text-sm font-semibold text-white bg-primary hover:bg-green-700 px-3 py-1.5 rounded-xl transition-colors justify-self-end"
                        >
                            <Droplet class="w-3.5 h-3.5" />
                            Confirmar
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal de confirmacion -->
        <div
            v-if="selected"
            class="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/45 md:px-4"
            @click.self="closeConfirm"
        >
            <div class="bg-surface rounded-t-3xl md:rounded-2xl shadow-xl w-full md:max-w-sm p-5 pb-7 md:pb-5 pb-safe">
                <div class="md:hidden w-10 h-1 rounded-full bg-black/15 mx-auto mb-4"></div>
                <h2 class="text-base font-bold text-ink mb-1">Confirmar riego</h2>
                <p class="text-sm text-muted mb-4">Recomendación del {{ selected.date }}</p>

                <label class="block text-sm font-semibold text-ink mb-1">Fecha de riego</label>
                <input
                    type="date"
                    v-model="form.irrigation_date"
                    :max="today"
                    class="w-full border border-line rounded-xl px-3 py-2 mb-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />

                <!-- Por tiempo (si hay caudal) -->
                <template v-if="hasCaudal">
                    <label class="block text-sm font-semibold text-ink mb-1">Tiempo de riego aplicado</label>
                    <div class="flex gap-2">
                        <div class="flex-1">
                            <input
                                type="number" v-model="form.hours" min="0" placeholder="0"
                                class="w-full border border-line rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                            <span class="block text-[11px] text-soft mt-1 text-center">horas</span>
                        </div>
                        <div class="flex-1">
                            <input
                                type="number" v-model="form.minutes" min="0" max="59" placeholder="0"
                                class="w-full border border-line rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                            <span class="block text-[11px] text-soft mt-1 text-center">minutos</span>
                        </div>
                    </div>
                </template>

                <!-- Por volumen (si no hay caudal) -->
                <template v-else>
                    <label class="block text-sm font-semibold text-ink mb-1">Volumen de riego aplicado</label>
                    <div class="relative">
                        <input
                            type="number" v-model="form.volume_m3" min="0" step="any" placeholder="0"
                            class="w-full border border-line rounded-xl px-3 py-2 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                        <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-soft">m³</span>
                    </div>
                    <p class="text-[11px] text-soft mt-1">
                        Este sector no tiene caudal cargado, así que confirmá el agua aplicada en m³.
                    </p>
                </template>

                <p v-if="formError" class="text-rust text-sm font-medium mt-3">{{ formError }}</p>

                <div class="flex gap-2 mt-5">
                    <button
                        @click="closeConfirm"
                        :disabled="submitting"
                        class="flex-1 text-sm font-semibold text-primary border-2 border-primary px-3 py-2 rounded-xl hover:bg-primary-soft transition-colors disabled:opacity-50"
                    >
                        Cancelar
                    </button>
                    <button
                        @click="submit"
                        :disabled="submitting"
                        class="flex-1 text-sm font-semibold text-white bg-primary hover:bg-green-700 px-3 py-2 rounded-xl transition-colors disabled:opacity-50"
                    >
                        {{ submitting ? 'Confirmando...' : 'Confirmar' }}
                    </button>
                </div>
            </div>
        </div>

    </div>
</template>
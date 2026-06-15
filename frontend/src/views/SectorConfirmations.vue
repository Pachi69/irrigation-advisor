<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Droplet } from 'lucide-vue-next'
import { useSectorConfirmations } from '../composables/useSectorConfirmations'
import UrgencyBadge from '../components/sector/UrgencyBadge.vue'
import ConfirmIrrigationModal from '../components/sector/ConfirmIrrigationModal.vue'

const route = useRoute()
const router = useRouter()
const {
    items, loading, error, selected, form, submitting, formError,
    today, hasCaudal, recLabel, recValue,
    openConfirm, closeConfirm, submit,
} = useSectorConfirmations(route.params.id)
</script>

<template>
    <div class="max-w-2xl lg:max-w-3xl mx-auto px-4 py-6">

        <div class="flex items-center justify-between mb-5">
            <button @click="router.push(`/sectors/${route.params.id}/recommendation`)"
                class="flex items-center gap-1 text-primary font-semibold text-sm hover:underline">
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
                <div v-for="item in items" :key="item.recommendation_id" class="bg-surface rounded-3xl border border-line p-4">
                    <div class="flex items-center justify-between mb-3.5">
                        <span class="text-sm font-bold text-ink">{{ item.date }}</span>
                        <UrgencyBadge :urgency="item.urgency" />
                    </div>
                    <div class="flex items-center justify-between bg-paper rounded-2xl px-3.5 py-3 mb-3.5">
                        <span class="app-label">{{ recLabel }}</span>
                        <span class="app-mono text-xl font-bold text-ink">{{ recValue(item) }}</span>
                    </div>
                    <button @click="openConfirm(item)"
                        class="w-full flex items-center justify-center gap-2 text-sm font-bold text-white bg-primary hover:bg-green-700 px-4 py-3 rounded-xl transition-colors">
                        <Droplet class="w-4 h-4" />
                        Confirmar riego
                    </button>
                </div>
            </div>

            <!-- DESKTOP -->
            <div class="hidden md:block">
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
                    <div v-for="item in items" :key="item.recommendation_id"
                        class="bg-surface rounded-2xl border border-line shadow-sm px-4 py-3 grid grid-cols-[6rem_1fr_7rem_auto] gap-3 items-center">
                        <span class="text-sm text-muted">{{ item.date }}</span>
                        <UrgencyBadge :urgency="item.urgency" class="justify-self-start" />
                        <span class="text-sm font-bold text-ink justify-self-end">{{ recValue(item) }}</span>
                        <button @click="openConfirm(item)"
                            class="flex items-center gap-1 text-sm font-semibold text-white bg-primary hover:bg-green-700 px-3 py-1.5 rounded-xl transition-colors justify-self-end">
                            <Droplet class="w-3.5 h-3.5" />
                            Confirmar
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <ConfirmIrrigationModal
            v-if="selected"
            :item="selected"
            :form="form"
            :has-caudal="hasCaudal"
            :today="today"
            :submitting="submitting"
            :form-error="formError"
            @close="closeConfirm"
            @submit="submit"
        />
    </div>
</template>
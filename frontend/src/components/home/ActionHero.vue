<script setup>
import { RouterLink } from 'vue-router'
import { ArrowRight, Plus } from 'lucide-vue-next'
import { irrigationAmount } from '../../utils/format'

defineProps({
    urgentSector: { type: Object, default: null },
    urgentCount: { type: Number, default: 0 },
    activeCount: { type: Number, default: 0 },
})
</script>

<template>
    <div class="relative overflow-hidden bg-ink text-white rounded-3xl p-6 md:p-7 min-h-[180px] md:min-h-[220px]">
        <div class="text-[11px] font-bold uppercase tracking-widest opacity-70 mb-2">
            Acción del día
        </div>

        <template v-if="urgentSector">
            <h2 class="text-xl md:text-[28px] font-bold tracking-tight leading-tight m-0 mb-1">
                {{ urgentCount }} {{ urgentCount === 1 ? 'sector necesita' : 'sectores necesitan' }} riego hoy
            </h2>
            <div class="text-sm opacity-70 mb-5 md:mb-6">
                <template v-if="activeCount - urgentCount > 0">
                    {{ activeCount - urgentCount }}
                    {{ (activeCount - urgentCount) === 1 ? 'está' : 'están' }} dentro de rango.
                </template>
                <template v-else>
                    Revisalos antes del mediodía.
                </template>
            </div>
            <div class="flex items-end justify-between gap-4 pt-4 md:pt-5 border-t border-white/12">
                <div>
                    <div class="text-xs opacity-65 mb-1">{{ urgentSector.fieldName }} · {{ urgentSector.name }}</div>
                    <div class="app-mono text-3xl md:text-[42px] font-bold tracking-tight leading-none">
                        {{ irrigationAmount(urgentSector.last_recommendation) }}
                    </div>
                </div>
                <RouterLink
                    :to="`/sectors/${urgentSector.id}/recommendation`"
                    class="bg-white text-ink font-bold text-sm px-4 py-2.5 rounded-xl inline-flex items-center gap-1.5"
                >
                    Ver <ArrowRight :size="14" />
                </RouterLink>
            </div>
        </template>

        <template v-else-if="activeCount === 0">
            <h2 class="text-xl md:text-[28px] font-bold tracking-tight leading-tight m-0 mb-1">
                Bienvenido a HydroSense.
            </h2>
            <div class="text-sm opacity-70 mb-5 md:mb-6">
                Registrá tu primer campo para empezar a recibir recomendaciones.
            </div>
            <RouterLink
                to="/fields/new"
                class="inline-flex items-center gap-1.5 bg-white text-ink font-bold text-sm px-4 py-2.5 rounded-xl"
            >
                <Plus :size="14" /> Registrar campo
            </RouterLink>
        </template>

        <template v-else>
            <h2 class="text-xl md:text-[28px] font-bold tracking-tight leading-tight m-0 mb-1">
                Todo en orden hoy.
            </h2>
            <div class="text-sm opacity-70">
                No se requiere riego en ninguno de tus campos.
            </div>
        </template>

        <!-- Decorative drop -->
        <svg class="absolute -top-10 -right-10 opacity-5 pointer-events-none" width="220" height="220" viewBox="0 0 32 32" fill="none">
            <path d="M16 3c-4 6-7 9-7 13a7 7 0 0 0 14 0c0-4-3-7-7-13z" fill="currentColor"/>
        </svg>
    </div>
</template>
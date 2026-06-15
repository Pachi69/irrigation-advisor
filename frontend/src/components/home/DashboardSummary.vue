<script setup>
import { Satellite } from 'lucide-vue-next'

defineProps({
    activeFieldsCount: { type: Number, default: 0 },
    totalArea: { type: [String, Number], default: '0.0' },
})
</script>

<template>
    <div class="hidden md:flex flex-col gap-3">
        <div class="bg-surface border border-line rounded-3xl px-5 py-4">
            <div class="app-label mb-2">Resumen</div>
            <div class="grid grid-cols-2 gap-3.5">
                <div>
                    <div class="app-label">Campos activos</div>
                    <div class="text-lg font-bold mt-1">{{ activeFieldsCount }}</div>
                </div>
                <div>
                    <div class="app-label">Superficie total</div>
                    <div class="app-mono text-lg font-bold mt-1">{{ totalArea }} 
                        <span class="text-sm text-muted font-semibold">ha</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="bg-primary-soft rounded-3xl px-5 py-3.5 flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-primary text-white flex items-center justify-center shrink-0">
                <Satellite :size="18" />
            </div>
            <div class="flex-1">
                <div class="text-xs font-bold uppercase tracking-wide text-primary">Sentinel-2</div>
                <div class="text-sm font-medium">Datos de NDVI semanales</div>
            </div>
        </div>
    </div>
</template>
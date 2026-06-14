<script setup>
import { RouterLink } from 'vue-router'
import { Droplet } from 'lucide-vue-next'

defineProps({ sectorId: { type: [String, Number], required: true } })
</script>

<template>
    <div class="hidden md:block bg-primary-soft rounded-3xl p-5">
        <div class="flex items-center gap-3 mb-2.5">
            <div class="w-8 h-8 rounded-xl bg-primary text-primary-ink flex items-center justify-center">
                <Droplet :size="16" />
            </div>
            <div class="text-[11px] font-bold uppercase tracking-wider text-primary">Confirmá el riego</div>
        </div>
        <p class="text-sm text-ink leading-relaxed mb-3.5">
            Cuando hayas regado, confirmá cuántos mm aplicaste para que recalibremos el balance hídrico.
        </p>
        <RouterLink :to="`/sectors/${sectorId}/confirmations`"
        class="w-full bg-primary text-primary-ink font-bold text-sm py-3 rounded-xl flex items-center justify-center gap-1.5">
            Confirmar riego
        </RouterLink>
    </div>
</template>
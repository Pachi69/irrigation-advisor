<script setup>
import { Bell } from 'lucide-vue-next'
defineEmits(['enable'])
</script>

<template>
    <div class="mb-4 bg-amber-soft border border-amber/30 rounded-2xl p-4 flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-amber text-white flex items-center justify-center shrink-0">
            <Bell :size="18" />
        </div>
        <div class="flex-1 min-w-0">
            <div class="text-sm font-bold text-ink">Activá las alertas de riego</div>
            <div class="text-xs text-muted">Te avisamos cuando hay que regar.</div>
        </div>
        <button @click="$emit('enable')" class="bg-amber text-white text-sm font-bold px-3 py-2 rounded-xl shrink-0">
            Activar
        </button>
    </div>
</template>
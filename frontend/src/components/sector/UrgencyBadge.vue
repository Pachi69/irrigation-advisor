<script setup>
import { computed } from 'vue'
import { URGENCY_LABEL } from '../../utils/labels'

const props = defineProps({
    urgency: { type: String, required: true },
})

const URG = {
    none:     { bg: 'var(--color-primary-soft)', fg: 'var(--color-primary)',   dot: 'var(--color-primary)' },
    low:      { bg: 'var(--color-primary-soft)', fg: 'var(--color-primary)',   dot: 'var(--color-primary)' },
    medium:   { bg: 'var(--color-amber-soft)',   fg: 'var(--color-amber-ink)', dot: 'var(--color-amber)' },
    high:     { bg: '#F1D8C4',                    fg: '#8A3D12',                dot: '#D8651C' },
    critical: { bg: 'var(--color-rust-soft)',    fg: 'var(--color-rust)',      dot: 'var(--color-rust)' },
}
const c = computed(() => URG[props.urgency] || URG.none)
</script>

<template>
    <span
        class="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full"
        :style="{ background: c.bg, color: c.fg }"
    >
        <span class="w-1.5 h-1.5 rounded-full" :style="{ background: c.dot }"></span>
        {{ URGENCY_LABEL[urgency] }}
    </span>
</template>
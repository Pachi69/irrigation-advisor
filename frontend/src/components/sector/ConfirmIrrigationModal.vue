<script setup>
defineProps({
    item: { type: Object, required: true },
    form: { type: Object, required: true },
    hasCaudal: { type: Boolean, required: true },
    today: { type: String, required: true },
    submitting: { type: Boolean, default: false },
    formError: { type: String, default: '' },
})
defineEmits(['close', 'submit'])
</script>

<template>
    <div
        class="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/45 md:px-4"
        @click.self="$emit('close')"
    >
        <div class="bg-surface rounded-t-3xl md:rounded-2xl shadow-xl w-full md:max-w-sm p-5 pb-7 md:pb-5 pb-safe">
            <div class="md:hidden w-10 h-1 rounded-full bg-black/15 mx-auto mb-4"></div>
            <h2 class="text-base font-bold text-ink mb-1">Confirmar riego</h2>
            <p class="text-sm text-muted mb-4">Recomendación del {{ item.date }}</p>

            <label class="block text-sm font-semibold text-ink mb-1">Fecha de riego</label>
            <input type="date" v-model="form.irrigation_date" :max="today"
                class="w-full border border-line rounded-xl px-3 py-2 mb-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />

            <!-- Por tiempo (si hay caudal) -->
            <template v-if="hasCaudal">
                <label class="block text-sm font-semibold text-ink mb-1">Tiempo de riego aplicado</label>
                <div class="flex gap-2">
                    <div class="flex-1">
                        <input type="number" v-model="form.hours" min="0" placeholder="0"
                            class="w-full border border-line rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                        <span class="block text-[11px] text-soft mt-1 text-center">horas</span>
                    </div>
                    <div class="flex-1">
                        <input type="number" v-model="form.minutes" min="0" max="59" placeholder="0"
                            class="w-full border border-line rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                        <span class="block text-[11px] text-soft mt-1 text-center">minutos</span>
                    </div>
                </div>
            </template>

            <!-- Por volumen (si no hay caudal) -->
            <template v-else>
                <label class="block text-sm font-semibold text-ink mb-1">Volumen de riego aplicado</label>
                <div class="relative">
                    <input type="number" v-model="form.volume_m3" min="0" step="any" placeholder="0"
                        class="w-full border border-line rounded-xl px-3 py-2 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                    <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-soft">m³</span>
                </div>
                <p class="text-[11px] text-soft mt-1">
                    Este sector no tiene caudal cargado, así que confirmá el agua aplicada en m³.
                </p>
            </template>

            <p v-if="formError" class="text-rust text-sm font-medium mt-3">{{ formError }}</p>

            <div class="flex gap-2 mt-5 mb-5">
                <button @click="$emit('close')" :disabled="submitting"
                    class="flex-1 text-sm font-semibold text-primary border-2 border-primary px-3 py-2 rounded-xl hover:bg-primary-soft transition-colors disabled:opacity-50">
                    Cancelar
                </button>
                <button @click="$emit('submit')" :disabled="submitting"
                    class="flex-1 text-sm font-semibold text-white bg-primary hover:bg-green-700 px-3 py-2 rounded-xl transition-colors disabled:opacity-50">
                    {{ submitting ? 'Confirmando...' : 'Confirmar' }}
                </button>
            </div>
        </div>
    </div>
</template>
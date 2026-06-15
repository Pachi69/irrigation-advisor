<script setup>
import FieldMapEditor from '../FieldMapEditor.vue'

defineProps({
    sector: { type: Object, required: true },
    modelValue: { default: null },
    saving: { type: Boolean, default: false },
    error: { type: String, default: '' },
})
const emit = defineEmits(['close', 'save', 'update:modelValue'])
</script>

<template>
    <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="emit('close')">
        <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto flex flex-col">
            <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                <h2 class="text-base font-bold text-gray-900">Polígono de "{{ sector.name }}"</h2>
                <button @click="emit('close')" class="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
            </div>

            <div class="p-4 flex-1 space-y-3">
                <p class="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5">
                    Corregí el perímetro del sector si el productor lo dibujó mal (caminos, zonas fuera del cuadro, etc.).
                </p>
                <FieldMapEditor :model-value="modelValue" @update:model-value="emit('update:modelValue', $event)" height="380px" />
                <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">
                    {{ error }}
                </div>
            </div>

            <div class="flex gap-3 px-5 py-4 border-t border-gray-100">
                <button @click="emit('close')" :disabled="saving"
                    class="flex-1 border-2 border-gray-200 text-gray-600 font-bold py-3 rounded-xl text-sm hover:border-gray-300 transition-colors disabled:opacity-50">
                    Cancelar
                </button>
                <button @click="emit('save')" :disabled="!modelValue || saving"
                    class="flex-1 bg-green-800 hover:bg-green-700 text-white font-bold py-3 rounded-xl text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                    {{ saving ? 'Guardando...' : 'Guardar polígono' }}
                </button>
            </div>
        </div>
    </div>
</template>
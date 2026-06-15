<script setup>
import { computed } from 'vue'
import { MapPin, Check } from 'lucide-vue-next'
import { CROP_LABELS } from '../../utils/labels'

const props = defineProps({
    field: { type: Object, required: true },
    savedIds: { type: Set, required: true },
    approvingId: { type: Number, default: null },
    approveError: { type: String, default: '' },
})
defineEmits(['edit', 'approve'])

const pendingCount = computed(() => (props.field.sectors || []).filter(s => s.status === 'pending').length)
</script>

<template>
    <div class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div class="bg-amber-400 px-4 py-2">
            <span class="text-xs font-bold uppercase tracking-wide text-amber-900">
                {{ pendingCount }} sector{{ pendingCount === 1 ? '' : 'es' }} por aprobar
            </span>
        </div>

        <div class="p-4">
            <h2 class="text-base font-bold text-gray-900 mb-0.5">{{ field.name }}</h2>
            <p class="text-xs text-gray-400 mb-3">
                {{ field.user.name }} · {{ field.user.email }}
            </p>

            <div class="space-y-2">
                <div v-for="s in field.sectors" :key="s.id" class="border border-gray-200 rounded-xl px-3 py-2.5">
                    <div class="flex items-center justify-between gap-3">
                        <div class="min-w-0">
                            <div class="text-sm font-semibold text-gray-800 truncate">{{ s.name }}</div>
                            <div class="text-xs text-gray-400">
                                {{ CROP_LABELS[s.crop_type] || s.crop_type }}<template v-if="s.variety"> · {{ s.variety }}</template> ·
                                {{ s.area_ha != null ? `${s.area_ha.toFixed(2)} ha` : 'sin área' }}
                            </div>
                        </div>
                        <div class="shrink-0">
                            <span v-if="s.status === 'active'"
                                class="flex items-center gap-1 text-xs font-semibold text-green-700 px-2.5 py-1.5 rounded-lg border border-green-700 bg-green-50 cursor-default">
                                <Check class="w-3.5 h-3.5" />
                                Aprobado
                            </span>
                            <span v-else-if="savedIds.has(s.id)"
                                class="flex items-center gap-1 text-xs font-semibold text-green-700 px-2.5 py-1.5 rounded-lg border border-green-700 bg-green-50 cursor-default">
                                <MapPin class="w-3.5 h-3.5" />
                                Guardado
                            </span>
                            <button v-else @click="$emit('edit', s)"
                                class="flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg transition-colors"
                                :class="s.polygon_geojson
                                    ? 'text-green-800 border border-green-700 hover:bg-green-50'
                                    : 'text-amber-700 border border-amber-400 hover:bg-amber-50'">
                                <MapPin class="w-3.5 h-3.5" />
                                {{ s.polygon_geojson ? 'Editar polígono' : 'Dibujar polígono' }}
                            </button>
                        </div>
                    </div>

                    <div v-if="s.status === 'pending'" class="mt-2.5">
                        <div v-if="approveError && approvingId === s.id" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2 rounded-lg mb-2">
                            {{ approveError }}
                        </div>
                        <button @click="$emit('approve', s)"
                            :disabled="!s.polygon_geojson || approvingId === s.id"
                            class="w-full bg-green-800 hover:bg-green-700 text-white font-bold py-2 rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                            {{ approvingId === s.id ? 'Aprobando...' : 'Aprobar sector' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
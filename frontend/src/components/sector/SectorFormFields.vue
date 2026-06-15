<script setup>
import { useSectorForm } from '../../composables/useSectorForm'

defineProps({
    form: { type: Object, required: true },
    disabled: { type: Boolean, default: false },
    saturationRequired: { type: Boolean, default: false },
    saturationHelp: {
        type: String,
        default: 'Actualizá esta fecha tras un riego completo para recalibrar el balance hídrico.',
    },
})

const { notifHours, todayStr } = useSectorForm()

const inputBase = 'w-full border-2 border-gray-200 rounded-xl px-3 py-3 text-base focus:outline-none focus:border-green-600 disabled:opacity-50 transition-colors'
const txtClass = inputBase + ' disabled:bg-gray-50'
const selClass = inputBase + ' bg-white'
const numClass = inputBase
</script>

<template>
    <!-- Nombre -->
    <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre del sector</label>
        <input v-model="form.name" type="text" required minlength="2" maxlength="255"
            placeholder="Ej: Cuadro Malbec norte" :disabled="disabled" :class="txtClass" />
    </div>

    <!-- Cultivo (slot, solo alta) + Variedad -->
    <div :class="$slots.crop ? 'grid grid-cols-2 gap-3' : ''">
        <slot name="crop" />
        <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Variedad</label>
            <input v-model="form.variety" type="text" maxlength="255" placeholder="Ej: Malbec"
                :disabled="disabled" :class="txtClass" />
        </div>
    </div>

    <!-- Riego -->
    <div class="grid grid-cols-2 gap-3">
        <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Tipo de riego</label>
            <select v-model="form.irrigation_type" required :disabled="disabled" :class="selClass">
                <option value="aspersion">Aspersión</option>
                <option value="superficial">Superficial</option>
            </select>
        </div>
        <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Malla antigranizo</label>
            <select v-model="form.hail_net_type" required :disabled="disabled" :class="selClass">
                <option value="none">Sin malla</option>
                <option value="open">Malla abierta</option>
                <option value="dense">Malla densa</option>
                <option value="color">Malla de color</option>
            </select>
        </div>
    </div>

    <!-- Caudal -->
    <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1.5">Caudal (L/s/ha)</label>
        <input v-model.number="form.flow_rate_ls_ha" type="number" min="0.1" step="0.1"
            placeholder="Dejar vacío si no lo sabés" :disabled="disabled" :class="numClass" />
        <p class="text-xs text-gray-400 mt-1.5">
            Caudal de la bomba dividido por las hectáreas del sector. Si lo dejás vacío, calculamos el volumen pero no el tiempo de riego.
        </p>
    </div>

    <!-- Ubicación / mapa (slot, solo alta) -->
    <slot name="map" />

    <!-- Último riego / lluvia -->
    <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1.5">Último riego completo o lluvia abundante</label>
        <input v-model="form.last_saturation_date" type="date" :max="todayStr"
            :required="saturationRequired" :disabled="disabled" :class="txtClass" />
        <p class="text-xs text-gray-400 mt-1.5">{{ saturationHelp }}</p>
    </div>

    <!-- Notificaciones -->
    <div class="grid grid-cols-2 gap-3">
        <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Hora de aviso</label>
            <select v-model="form.notification_hour" :disabled="disabled" :class="selClass">
                <option v-for="h in notifHours" :key="h" :value="`${String(h).padStart(2, '0')}:00:00`">
                    {{ String(h).padStart(2, '0') }}:00
                </option>
            </select>
        </div>
        <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Frecuencia (días)</label>
            <input v-model.number="form.notification_frequency_days" type="number" min="1" step="1"
                :disabled="disabled" :class="numClass" />
        </div>
    </div>
    <p class="text-xs text-gray-400 mt-2">Te avisamos a esa hora, cada tantos días, solo si hay que regar.</p>
</template>
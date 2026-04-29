<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getFieldById, updateField } from '../services/fields'

const route = useRoute()
const router = useRouter()

const form = ref(null)
const loading = ref(true)
const error = ref('')
const saving = ref(false)

const CROP_OPTIONS = [
    {value: 'vine', label: 'Vid'},
    {value: 'peach', label: 'Durazno'},
    {value: 'alfalfa', label: 'Alfalfa'},
]

const SOIL_OPTIONS = [
    {value: 'sandy', label: 'Arenoso'},
    {value: 'loamy', label: 'Franco'},
    {value: 'clay', label: 'Arcilloso'},
]

const IRRIGATION_OPTIONS = [
    {value: 'drip', label: 'Goteo'},
    {value: 'sprinkler', label: 'Aspersión'},
    {value: 'flood', label: 'Surco'},
]

onMounted(async () => {
    try {
        const field = await getFieldById(route.params.id)
        form.value = {
            name: field.name,
            crop_type: field.crop_type,
            area_ha: field.area_ha,
            irrigation_type: field.irrigation_type,
            soil_type: field.soil_type,
            has_hail_net: field.has_hail_net,
            planting_date: field.planting_date,
        }
    } catch {
        error.value = 'No se pudo cargar el campo'
    } finally {
        loading.value = false
    }
})

async function handleSubmit() {
    saving.value = true
    error.value = ''
    try {
        await updateField(route.params.id, {
            ...form.value,
            area_ha: Number(form.value.area_ha),
        })
        router.push('/fields')
    } catch {
        error.value = 'No se pudo guardar los cambios, Intenta nuevamente'
    } finally {
        saving.value = false
    }
}

</script>

<template>
    <div class="form-container">
        <h1>Editar Campo</h1>

        <div v-if="loading" class="center">Cargando...</div>
        <div v-else-if="error && !form" class="error">{{ error }}</div>

        <form v-else-if="form" @submit.prevent="handleSubmit">
            <label>
                Nombre del campo
                <input v-model="form.name" type="text" required minlength="2" maxlength="255" :disabled="saving" />
            </label>

            <label>
                Cultivo
                <select v-model="form.crop_type" required :disabled="saving">
                    <option v-for="o in CROP_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
            </label>

            <label>
                Tipo de suelo
                <select v-model="form.soil_type" required :disabled="saving">
                    <option v-for="o in SOIL_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
            </label>

            <label>
                Tipo de riego
                <select v-model="form.irrigation_type" required :disabled="saving">
                    <option v-for="o in IRRIGATION_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
            </label>

            <label>
                Superficie (hectáreas)
                <input v-model="form.area_ha" type="number" required min="0.01" max="10000" step="0.01" :disabled="saving">
            </label>
            
            <label>
                Fecha de siembra o brotación
                <input v-model="form.planting_date" type="date" required :disabled="saving">
            </label>

            <label class="checkbox">
                <input v-model="form.has_hail_net" type="checkbox" :disabled="saving">
                El campo tiene malla antigranizo
            </label>

            <p v-if="error" class="error">{{ error }}</p>

            <div class="actions">
                <button type="button" @click="router.push('/fields')" :disabled="saving" class="btn-secondary">
                    Cancelar
                </button>
                <button type="submit" :disabled="saving" class="btn-primary">
                    {{ saving ? 'Guardando...' : 'Guardar cambios' }}
                </button>
            </div>
        </form>
    </div>
</template>

<style scoped>
.form-container { max-width: 500px; margin: 0 auto; }
form { display: flex; flex-direction: column; gap: 1rem; }
label { display: flex; flex-direction: column; gap: 0.25rem; }
label.checkbox { flex-direction: row; align-items: center; gap: 0.5rem; }
input, select {
    padding: 0.5rem; font-size: 1rem; border: 1px solid #ccc; border-radius: 4px;
}
.actions { display: flex; gap: 0.75rem; margin-top: 0.5rem; }
.btn-primary, .btn-secondary {
    padding: 0.75rem 1.25rem; font-size: 1rem; cursor: pointer;
    border-radius: 4px; border: none; flex: 1;
}
.btn-primary { background: #2e7d32; color: white; }
.btn-primary:hover:not(:disabled) { background: #1b5e20; }
.btn-secondary { background: #e0e0e0; color: #333; }
.btn-secondary:hover:not(:disabled) { background: #bdbdbd; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
.error { color: #c00; margin: 0; }
.center { text-align: center; padding: 2rem; color: #666; }
</style>
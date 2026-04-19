<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createField } from '../services/fields'

const router = useRouter()

const form = ref({
    name: '',
    crop_type: 'vine',
    area_ha: null,
    irrigation_type: 'drip',
    soil_type: 'loamy',
    has_hail_net: false,
    planting_date: ''
})

const loading = ref(false)
const error = ref('')

async function handleSubmit() {
    error.value = ''
    loading.value = true
    try {
        await createField({
            ...form.value,
            area_ha: Number(form.value.area_ha),
        })
        router.push('/fields')
    } catch (err) {
        if (err.response?.status === 422) {
            error.value = 'Datos invalidos. Revisa el formulario.'
        } else {
            error.value = 'Error al registrar el campo. Intenta nuevamente.'
        }
    } finally {
        loading.value = false
    }
}

function cancel() {
    router.push('/fields')
}
</script>

<template>
    <div class="form-container">
        <h1>Registrar Nuevo Campo</h1>
        <p class="hint">
            Después del registr, un administrador asignará el polígono geografico
            para activar el procesamiento satelital.
        </p>

        <form @submit.prevent="handleSubmit">
            <label>
                Nombre del campo
                <input
                    v-model="form.name"
                    type="text"
                    required
                    minlength="2"
                    maxlength="255"
                    placeholder="Ej: Finca los Álamos"
                    :disabled="loading"
                />
            </label>

            <label>
                Cultivo
                <select v-model="form.crop_type" required :disabled="loading">
                    <option value="vine">Vid</option>
                    <option value="peach">Durazno</option>
                </select>
            </label>

            <label>
                Tipo de suelo
                <select v-model="form.soil_type" required :disabled="loading">
                    <option value="sandy">Arenoso</option>
                    <option value="loamy">Franco</option>
                    <option value="clay">Arcilloso</option>
                </select>
            </label>

            <label>
                Tipo de riego
                <select v-model="form.irrigation_type" required :disabled="loading">
                    <option value="drip">Goteo</option>
                    <option value="sprinkler">Aspersión</option>
                    <option value="flood">Surco</option>
                </select>
            </label>

            <label>
                Superficie (hectáreas)
                <input
                    v-model="form.area_ha"
                    type="number"
                    required
                    min="0.01"
                    max="10000"
                    step="0.01"
                    placeholder="Ej: 2.5"
                    :disabled="loading"
                />
            </label>

            <label>
                Fecha de siembra o brotación
                <input
                    v-model="form.planting_date"
                    type="date"
                    required
                    :disabled="loading"
                />
            </label>

            <label class="checkbox">
                <input
                    v-model="form.has_hail_net"
                    type="checkbox"
                    :disabled="loading"
                />
                El campo tiene malla antigranizo
            </label>

            <div class="actions">
                <button type="button" @click="cancel" :disabled="loading" class="btn-secondary">
                    Cancelar
                </button>
                <button type="submit" :disabled="loading" class="btn-primary">
                    {{ loading ? 'Guardando...' : 'Registrar campo' }}
                </button>
            </div>

            <p v-if="error" class="error">{{ error }}</p>
        </form>
    </div>
</template>

<style scoped>
.form-container { max-width: 500px; margin: 0 auto; }
.hint {
  background: #e3f2fd; padding: 0.75rem; border-radius: 4px;
  font-size: 0.9rem; color: #0d47a1; margin-bottom: 1.5rem;
}
form { display: flex; flex-direction: column; gap: 1rem; }
label { display: flex; flex-direction: column; gap: 0.25rem; }
label.checkbox {
  flex-direction: row; align-items: center; gap: 0.5rem;
}
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
</style>
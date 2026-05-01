<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createField } from '../services/fields'
import FieldMapEditor from '../components/FieldMapEditor.vue'

const router = useRouter()

const form = ref({
    name: '',
    crop_type: 'vine',
    area_ha: null,
    irrigation_type: 'drip',
    soil_type: 'loamy',
    has_hail_net: false,
    planting_date: '',
    polygon_geojson: null,
})

const loading = ref(false)
const error = ref('')
const showMapModal = ref(false)

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
            Dibujá el perímetro de tu campo en el mapa para agilizar la aprobación.
            El administrador revisará el polígono antes de activar el procesamiento satelital.
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
                    <option value="alfalfa">Alfalfa</option>
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

            <div class="map-field">
                <span class="map-label">Ubicación del campo</span>
                <span class="field-hint">Marcá el perímetro de tu campo para agilizar la aprobación.</span>
                <button type="button" class="btn-map" @click="showMapModal = true">
                    Abrir mapa y marcar campo
                </button>
                <span v-if="form.polygon_geojson" class="map-ok">Campo marcado correctamente</span>
                <span v-else class="map-empty">Sin marcar aún</span>
            </div>

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

        <div v-if="showMapModal" class="map-backdrop" @click.self="showMapModal = false">
            <div class="map-modal">
                <header class="map-modal-header">
                    <h2>Marcá el perímetro de tu campo</h2>
                    <button type="button" class="btn-close" @click="showMapModal = false">X</button>
                </header>
                <p class="map-modal-hint">
                    Tocá el ícono de polígono en el panel izquierdo del mapa, luego hacé clic
                    en cada esquina de tu campo y cerrá el contorno al final.
                </p>
                <FieldMapEditor v-model="form.polygon_geojson" height="500px" />
                <footer class="map-modal-footer">
                    <button
                        type="button"
                        class="btn-primary btn-confirm-map"
                        :disabled="!form.polygon_geojson"
                        @click="showMapModal = false"
                    >
                        {{ form.polygon_geojson ? 'Confirmar ubicación' : 'Dibujá el campo primero' }}
                    </button>
                </footer>
            </div>
        </div>
    </div>
</template>

<style scoped>
.form-container { max-width: 500px; margin: 0 auto; }
.hint {
  background: #e3f2fd; padding: 0.75rem; border-radius: 4px;
  font-size: 0.9rem; color: #0d47a1; margin-bottom: 1.5rem;
}
.field-hint {
    font-size: 0.82rem; color: #666; margin-bottom: 0.35rem;
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
.map-field { display: flex; flex-direction: column; gap: 0.25rem; }
.map-label { font-size: 1rem; }
.btn-map {
    padding: 0.6rem 1rem; background: #e8f5e9; color: #2e7d32;
    border: 1px solid #2e7d32; border-radius: 4px; cursor: pointer;
    font-size: 0.95rem; text-align: left;
}
.btn-map:hover { background: #c8e6c9; }
.map-ok { font-size: 0.85rem; color: #2e7d32; font-weight: 500; }
.map-empty { font-size: 0.85rem; color: #999; }

.map-backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.55);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000;
}
.map-modal {
    background: white; border-radius: 8px;
    width: min(820px, 96vw);
    max-height: 92vh; overflow-y: auto;
    display: flex; flex-direction: column;
}
.map-modal-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1rem 1.25rem; border-bottom: 1px solid #eee;
}
.map-modal-header h2 { margin: 0; font-size: 1.1rem; color: #2e7d32; }
.btn-close {
    background: none; border: none; font-size: 1.2rem;
    cursor: pointer; color: #666;
}
.map-modal-hint {
    font-size: 0.88rem; color: #555; margin: 0;
    padding: 0.75rem 1.25rem; background: #f9f9f9;
    border-bottom: 1px solid #eee;
}
.map-modal-footer {
    padding: 1rem 1.25rem; border-top: 1px solid #eee;
    display: flex; justify-content: flex-end;
}
.btn-confirm-map {
    padding: 0.7rem 1.5rem; font-size: 1rem;
}
</style>
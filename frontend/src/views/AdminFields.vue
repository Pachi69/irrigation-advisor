<script setup> 
import { ref, onMounted } from 'vue'
import { listPendingFields, approveField } from '../services/admin'
import FieldMapEditor from '../components/FieldMapEditor.vue'


const fields = ref([])
const loading = ref(true)
const error = ref('')

const approvingField = ref(null)
const polygonGeoJSON = ref(null)
const approving = ref(false)
const approveError = ref('')

const CROP_LABELS = { vine: 'Vid', peach: 'Durazno', alfalfa: 'Alfalfa' }
const SOIL_LABELS = { sandy: 'Arenoso', clay: 'Arcilloso', loamy: 'Franco' }
const IRRIGATION_LABELS = { drip: 'Goteo', sprinkler: 'Aspersión', flood: 'Surco' }

async function loadPending() {
    error.value = ''
    loading.value = true
    try {
        fields.value = await listPendingFields()
    } catch (err) {
        error.value = 'No se pudieron cargar los campos. Intente nuevamente.'
    } finally {
        loading.value = false
    }
}

function openApproveModal(field) {
    approvingField.value = field
    polygonGeoJSON.value = field.polygon_geojson || null
    approveError.value = ''
}

function closeApproveModal() {
    approvingField.value = null
}

async function confirmApproval() {
    if (!approvingField.value || !polygonGeoJSON.value) return
    approving.value = true
    approveError.value = ''
    try {
        await approveField(approvingField.value.id, polygonGeoJSON.value)
        // Sacamos el campo aprobado de la lista de pendientes
        fields.value = fields.value.filter(f => f.id !== approvingField.value.id)
        closeApproveModal()
    } catch (err) {
        approveError.value = err.response?.data?.detail || err.message || 'Error al aprobar el campo'
    } finally {
        approving.value = false
    }
}

onMounted(loadPending)
</script>

<template>
    <div class="admin-container">
        <header class="admin-header">
            <h1>Panel admin | Campos pendientes</h1>
            <button @click="loadPending" class="btn-secondary">Recargar</button>
        </header>

        <p v-if="loading">Cargando...</p>
        <p v-else-if="error" class="error">{{ error }}</p>
        <p v-else-if="fields.length === 0" class="empty">No hay campos pendientes.</p>

        <ul v-else class="field-list">
            <li v-for="field in fields" :key="field.id" class="field-card">
                <div class="field-head">
                    <h2>{{ field.name }}</h2>
                    <span class="status status-pending">Pendiente</span>
                </div>

                <p class="owner">
                    Dueño: <strong>{{ field.user.email }}</strong>
                    &lt;{{ field.user.name }}&gt;
                </p>

                <dl class="field-info">
                    <div><dt>Cultivo:</dt><dd>{{ CROP_LABELS[field.crop_type] }}</dd></div>
                    <div><dt>Suelo:</dt><dd>{{ SOIL_LABELS[field.soil_type] }}</dd></div>
                    <div><dt>Riego:</dt><dd>{{ IRRIGATION_LABELS[field.irrigation_type] }}</dd></div>
                    <div><dt>Superficie:</dt><dd>{{ field.area_ha }} ha</dd></div>
                    <div><dt>Siembra/brotación:</dt><dd>{{ field.planting_date }}</dd></div>
                    <div><dt>Malla antigranizo:</dt><dd>{{ field.has_hail_net ? 'Sí' : 'No' }}</dd></div>
                </dl>

                <div class="actions">
                    <button class="btn-primary" @click="openApproveModal(field)">Aprobar</button>
                </div>
            </li>
        </ul>

        <!-- Modal de aprobación -->
         <div v-if="approvingField" class="modal-backdrop" @click.self="closeApproveModal">
            <div class="modal">
                <header class="modal-header">
                    <h2>Aprobar "{{ approvingField.name }}"</h2>
                    <button class="btn-close" @click="closeApproveModal" aria-label="Cerrar">X</button>
                </header>

                <div class="modal-body">
                    <p class="map-hint">
                        Dibujá el perímetro del campo. Usá el ícono de polígono
                        o rectángulo en el panel izquierdo del mapa.
                    </p>
                    <FieldMapEditor v-model="polygonGeoJSON" height="380px" />
                    <p v-if="approveError" class="error">{{ approveError }}</p>
                </div>

                <footer class="modal-footer">
                    <button class="btn-secondary" @click="closeApproveModal" :disabled="approving">Cancelar</button>
                    <button 
                        class="btn-primary" 
                        @click="confirmApproval" 
                        :disabled="!polygonGeoJSON || approving"
                    > 
                        {{ approving ? 'Aprobando...' : 'Confirmar aprobacion' }}
                    </button>
                </footer>
            </div>
         </div>
    </div>
</template>

<style scoped>
.admin-container { max-width: 900px; margin: 0 auto; }
.admin-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 1.5rem;
}
.btn-secondary {
    padding: 0.5rem 1rem; background: #fff; color: #2e7d32;
    border: 1px solid #2e7d32; border-radius: 4px; cursor: pointer;
}
.btn-primary {
    padding: 0.5rem 1rem; background: #2e7d32; color: white;
    border: 0; border-radius: 4px; cursor: pointer;
}
.btn-primary:disabled { background: #9e9e9e; cursor: not-allowed; }
.empty { color: #666; }
.error { color: #c00; }
.field-list { list-style: none; padding: 0; display: grid; gap: 1rem; }
.field-card {
    border: 1px solid #ddd; border-radius: 8px; padding: 1rem; background: white;
}
.field-head {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.5rem;
}
.field-head h2 { margin: 0; font-size: 1.2rem; }
.owner { margin: 0 0 0.75rem; color: #555; font-size: 0.9rem; }
.status { font-size: 0.85rem; padding: 0.2rem 0.6rem; border-radius: 12px; }
.status-pending { background: #fff3cd; color: #856404; }
.field-info {
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem 1rem; margin: 0 0 1rem;
}
.field-info > div { display: flex; flex-direction: column; }
.field-info dt { font-size: 0.8rem; color: #666; }
.field-info dd { margin: 0; font-weight: 500; }
.actions { display: flex; justify-content: flex-end; }

.modal-backdrop {
    position: fixed; inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000;
}
.modal {
    background: white; border-radius: 8px;
    width: min(750px, 96vw);
    max-height: 90vh; overflow-y: auto;
    display: flex; flex-direction: column;
}
.modal-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1rem 1.25rem; border-bottom: 1px solid #eee;
}
.modal-header h2 { margin: 0; font-size: 1.1rem; }
.btn-close {
    background: transparent; border: 0; font-size: 1.2rem;
    cursor: pointer; color: #666;
}
.modal-body {
    padding: 1rem 1.25rem;
    display: flex; flex-direction: column; gap: 0.75rem;
}
.modal-body label { font-weight: 500; font-size: 0.9rem; }
.modal-body textarea {
    width: 100%; font-family: monospace; font-size: 0.85rem;
    padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;
    resize: vertical;
}
.preview {
    padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.9rem;
}
.preview-ok { background: #d4edda; color: #155724; }
.preview-error { background: #f8d7da; color: #721c24; }
.preview-hint { background: #f0f0f0; color: #666; font-style: italic; }
.modal-footer {
    display: flex; justify-content: flex-end; gap: 0.5rem;
    padding: 1rem 1.25rem; border-top: 1px solid #eee;
}
.map-hint {
    font-size: 0.875rem;
    color: #555;
    margin: 0;
    background: #f5f5f5;
    padding: 0.5rem 0.75rem;
    border-radius: 4px;
}
</style>

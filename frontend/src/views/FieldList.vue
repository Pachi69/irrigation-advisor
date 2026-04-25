<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { listMyFields } from '../services/fields'

const fields = ref([])
const loading = ref(true)
const error = ref('')

const CROP_LABELS = { vine: 'Vid', peach: 'Durazno' }
const SOIL_LABELS = { sandy: 'Arenoso', clay: 'Arcilloso', loamy: 'Franco' }
const IRRIGATION_LABELS = { drip: 'Goteo', sprinkler: 'Aspersión', flood: 'Surco' }
const STATUS_LABELS = { pending: 'Pendiente de aprobación', active: 'Activo', inactive: 'Inactivo' }

async function loadFields() {
    error.value = ''
    loading.value = true
    try {
        fields.value = await listMyFields()
    } catch (err) {
        error.value = 'No se pudieron cargar los campos. Intente nuevamente.'
    } finally {
        loading.value = false
    }
}

onMounted(loadFields)
</script>

<template>
    <div class="fields-container">
        <header class="fields-header">
            <h1>Mis Campos</h1>
            <RouterLink to="/fields/new" class="btn-primary">+ Registrar Campo</RouterLink>
        </header>
        
        <p v-if="loading">Cargando...</p>
        <p v-else-if="error" class="error">{{ error }}</p>

        <p v-else-if="fields.length === 0" class="empty">No tienes campos registrados.
            <RouterLink to="/fields/new" >+ Registrá el primero</RouterLink>
        </p>

        <ul v-else class="field-list">
            <li v-for="field in fields" :key="field.id" class="field-card">
                <div class="field-head">
                    <h2>{{ field.name }}</h2>
                    <span :class="['status', `status-${field.status}`]">
                        {{ STATUS_LABELS[field.status] }}
                    </span>
                </div>
                <dl class="field-info">
                    <div><dt>Cultivo:</dt><dd>{{ CROP_LABELS[field.crop_type] }}</dd></div>
                    <div><dt>Suelo:</dt><dd>{{ SOIL_LABELS[field.soil_type] }}</dd></div>
                    <div><dt>Riego:</dt><dd>{{ IRRIGATION_LABELS[field.irrigation_type] }}</dd></div>
                    <div><dt>Superficie</dt><dd>{{ field.area_ha }} ha</dd></div>
                    <div><dt>Siembra/brotación</dt><dd>{{ field.planting_date }}</dd></div>
                    <div><dt>Malla antigranizo</dt><dd>{{ field.has_hail_net ? 'Sí' : 'No' }}</dd></div>
                </dl>
                <div class="field-actions" v-if="field.status === 'active'">
                    <RouterLink :to="`/fields/${field.id}/recommendation`" class="btn-recommendation">
                        Ver recomendación de hoy ->
                    </RouterLink>
                </div>
            </li>
        </ul>
    </div>
</template>

<style scoped>
.fields-container { max-width: 800px; margin: 0 auto; }
.fields-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1.5rem;
}
.btn-primary {
  padding: 0.5rem 1rem; background: #2e7d32; color: white;
  text-decoration: none; border-radius: 4px;
}
.btn-primary:hover { background: #1b5e20; }
.empty { color: #666; }
.error { color: #c00; }
.field-list { list-style: none; padding: 0; display: grid; gap: 1rem; }
.field-card {
  border: 1px solid #ddd; border-radius: 8px; padding: 1rem;
  background: white;
}
.field-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.75rem;
}
.field-head h2 { margin: 0; font-size: 1.2rem; }
.status {
  font-size: 0.85rem; padding: 0.2rem 0.6rem; border-radius: 12px;
}
.status-pending { background: #fff3cd; color: #856404; }
.status-active { background: #d4edda; color: #155724; }
.status-inactive { background: #e2e3e5; color: #383d41; }
.field-info {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem 1rem;
  margin: 0;
}
.field-info > div { display: flex; flex-direction: column; }
.field-info dt { font-size: 0.8rem; color: #666; }
.field-info dd { margin: 0; font-weight: 500; }

.field-actions { margin-top: 0.75rem; }
.btn-recommendation {
    display: inline-block;
    padding: 0.4rem 0.9rem;
    background: #2e7d32;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-size: 0.9rem;
}
.btn-recommendation:hover { background: #1b5e20; }
</style>
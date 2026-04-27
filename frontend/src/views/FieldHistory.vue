<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRecommendationHistory } from '../services/fields';

const route = useRoute()    
const router = useRouter()

const history = ref([])
const loading = ref(true)
const error = ref('')

const URGENCY_LABEL = {
    low: 'Sin urgencia',
    medium: 'Moderada',
    high: 'Alta',
    critical: 'Critico',
}

onMounted(async () => {
    try {
        history.value = await getRecommendationHistory(route.params.id)
    } catch {
        error.value = 'No se pudo cargar el historial'
    } finally {
        loading.value = false
    }
})
</script>

<template>
    <div class="history-page">
        <header class="history-header">
            <button class="btn-back" @click="router.push(`/fields/${route.params.id}/recommendation`)"> <- Recomendacion</button>
            <h1>Historial</h1>
        </header>

        <div v-if="loading" class="center">Cargando historial ...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else-if="history.length === 0" class="center">Sin historial disponible</div>

        <ul v-else class="history-list">
            <li v-for="item in history" :key="item.id" class="history-item">
                <span class="item-date">{{ item.date }}</span>
                <span :class="['item-urgency', `urgency-${item.urgency}`]">{{ URGENCY_LABEL[item.urgency] }}</span>
                <span class="item-deficit" v-if="item.taw_mm">
                    {{ Math.round((item.water_deficit_mm / item.taw_mm) * 100) }}% déficit
                </span>
                <span class="item-mm">{{ item.recommended_irrigation_mm > 0 ? item.recommended_irrigation_mm + 'mm': 'Sin riego' }}</span>
            </li>
        </ul>
    </div>
</template>

<style scoped>
.history-page {
    max-width: 600px;
    margin: 0 auto;
    padding: 1rem;
    font-family: sans-serif;
}
.history-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.history-header h1 { font-size: 1.2rem; margin: 0; color: #2e7d32; }
.btn-back {
    background: none;
    border: none;
    color: #2e7d32;
    font-size: 0.95rem;
    cursor: pointer;
    padding: 0;
}
.history-list {
    list-style: none;
    margin: 0;
    padding: 0;
}
.history-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    background: white;
}
.item-date { font-size: 0.9rem; color: #555; }
.item-urgency {
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
}
.urgency-low      { background: #d4edda; color: #155724; }
.urgency-medium   { background: #fff3cd; color: #856404; }
.urgency-high     { background: #ffe0b2; color: #e65100; }
.urgency-critical { background: #ffcdd2; color: #c62828; }
.item-deficit { font-size: 0.85rem; color: #666; }
.item-mm { font-size: 0.9rem; font-weight: 600; color: #333; }
.center { text-align: center; padding: 2rem; color: #666; }
.error  { color: #c00; text-align: center; padding: 1rem; }
</style>
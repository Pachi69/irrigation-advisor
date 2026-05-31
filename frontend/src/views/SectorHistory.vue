<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { getRecommendationHistory } from '../services/sectors'
import { ArrowLeft, BarChart2 } from 'lucide-vue-next'
import { URGENCY_LABEL } from '../utils/labels'

const route = useRoute()
const router = useRouter()

const history = ref([])
const loading = ref(true)
const error = ref('')

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
    <div class="max-w-2xl lg:max-w-3xl mx-auto px-4 py-6">

        <div class="flex items-center justify-between mb-5">
            <button
                @click="router.push(`/sectors/${route.params.id}/recommendation`)"
                class="flex items-center gap-1 text-green-800 font-semibold text-sm hover:underline"
            >
                <ArrowLeft class="w-4 h-4" />
                Recomendación
            </button>
            <h1 class="text-base font-bold text-gray-900">Historial</h1>
            <RouterLink
                :to="`/sectors/${route.params.id}/chart`"
                class="flex items-center gap-1 text-sm font-semibold text-green-800 border-2 border-green-800 px-3 py-1.5 rounded-xl hover:bg-green-50 transition-colors"
            >
                <BarChart2 class="w-3.5 h-3.5" />
                Gráfico
            </RouterLink>
        </div>

        <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">Cargando historial...</div>
        <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">{{ error }}</div>
        <div v-else-if="history.length === 0" class="text-center py-12 text-gray-400 text-sm">Sin historial disponible.</div>

        <div v-else class="space-y-2">
            <div
                v-for="item in history"
                :key="item.id"
                class="bg-white rounded-2xl border border-gray-200 shadow-sm px-4 py-3 flex items-center justify-between"
            >
                <span class="text-sm text-gray-500 w-24 shrink-0">{{ item.date }}</span>

                <span :class="[
                'text-xs font-bold px-2.5 py-1 rounded-full',
                item.urgency === 'low'      ? 'bg-green-100 text-green-800' :
                item.urgency === 'medium'   ? 'bg-amber-100 text-amber-800' :
                item.urgency === 'high'     ? 'bg-orange-100 text-orange-800' :
                                                'bg-red-100 text-red-700'
                ]">
                {{ URGENCY_LABEL[item.urgency] }}
                </span>

                <span class="text-xs text-gray-400 w-16 text-center">
                {{ item.taw_mm ? Math.round((item.water_deficit_mm / item.taw_mm) * 100) + '% déf.' : '—' }}
                </span>

                <span class="text-sm font-bold text-gray-900 w-16 text-right">
                {{ item.recommended_irrigation_mm > 0 ? item.recommended_irrigation_mm + ' mm' : 'Sin riego' }}
                </span>
            </div>
        </div>

    </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { listMyFields } from '../services/fields'
import { Plus, ChevronRight, Clock} from 'lucide-vue-next'
import { CROP_LABELS, SOIL_LABELS, STATUS_LABELS } from '../utils/labels'

const fields = ref([])
const loading = ref(true)
const error = ref('')

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

const hasPending = computed(() => fields.value.some(f=> f.status === 'pending'))
</script>

<template>
    <div class="max-w-2xl lg:max-w-5xl mx-auto px-4 py-6">

        <!-- Header -->
        <div class="flex items-center justify-between mb-5">
            <h1 class="text-xl font-bold text-gray-900">Mis campos</h1>
            <RouterLink
                v-if="!hasPending"
                to="/fields/new"
                class="flex items-center gap-1.5 bg-green-800 hover:bg-green-700 text-white text-sm font-bold px-3 py-2 rounded-xl transition-colors"
            >
                <Plus class="w-4 h-4" />
                Registrar Campo
            </RouterLink>
            <span
                v-else
                class="flex items-center gap-1.5 bg-gray-200 text-gray-400 text-sm font-bold px-3 py-2 rounded-xl cursor-not-allowed"
                title="Tenes un campo pendiente de aprobacion"
            >
                <Plus class="w-4 h-4" />
                Registrar Campo
            </span>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">
            Cargando campos...
        </div>

        <!-- Error -->
        <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-4 py-3 rounded-xl">
            {{ error }}
        </div>

        <!-- Empty -->
        <div v-else-if="fields.length === 0" class="text-center py-12">
            <p class="text-gray-500 text-sm mb-3">No tenés campos registrados.</p>
            <RouterLink
                to="/fields/new"
                class="inline-flex items-center gap-1.5 bg-green-800 hover:bg-green-700 text-white text-sm font-bold px-4 py-2.5 rounded-xl transition-colors"
            >
                <Plus class="w-4 h-4" />
                Registrá el primero
            </RouterLink>
        </div>

        <!-- Lista de campos -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="field in fields" :key="field.id" class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                
                <!-- Banner de estado -->
                <div 
                    :class="[
                        'px-4 py-2 flex items-center justify-between',
                        field.status === 'active' ? 'bg-green-700' :
                        field.status === 'pending' ? 'bg-amber-400' :
                        'bg-gray-300'       
                    ]"
                >
                    <div class="flex items-center gap-1.5">
                        <Clock v-if="field.status === 'pending'" class="w-3.5 h-3.5 text-amber-900" />
                        <span
                            :class="[
                                'text-xs font-bold uppercase tracking-wide',
                                field.status === 'active' ? 'text-white':
                                field.status === 'pending' ? 'text-amber-900':
                                'text-gray-600'
                            ]"
                        >
                            {{ STATUS_LABELS[field.status] }}
                        </span>
                    </div>
                </div>

                <!-- Contenido -->
                <div class="p-4">
                    <h2 class="text-base font-bold text-gray-900 mb-3">{{ field.name }}</h2>

                    <div class="grid grid-cols-2 gap-x-4 gap-y-2.5 mb-4">
                        <div>
                            <p class="text-xs text-gray-400">Cultivos</p>
                            <p class="text-sm font-semibold text-gray-800"> {{ CROP_LABELS[field.crop_type] }}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-400">Superficie</p>
                            <p class="text-sm font-semibold text-gray-800">
                                {{ field.area_ha != null ? `${field.area_ha.toFixed(2)} ha` : '—' }}
                            </p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-400">Suelo</p>
                            <p class="text-sm font-semibold text-gray-800">{{ SOIL_LABELS[field.soil_type] }}</p>
                        </div>
                    </div>

                    <!-- Acciones (solo activos) -->
                    <div v-if="field.status === 'active'" class="flex gap-2">
                        <RouterLink
                            :to="`/fields/${field.id}/recommendation`"
                            class="flex-1 flex items-center justify-center gap-1.5 bg-green-800 hover:bg-green-700 text-white font-bold py-2.5 rounded-xl text-sm transition-colors"
                        >
                            Ver Recomendación
                            <ChevronRight class="w-4 h-4" />
                        </RouterLink>
                        <RouterLink
                            :to="`/fields/${field.id}/edit`"
                            class="border-2 border-gray-200 hover:border-gray-300 text-gray-600 font-semibold py-2.5 px-4 rounded-xl text-sm transition-colors"
                        >
                            Editar
                        </RouterLink>
                    </div>

                    <!-- Pendiente: mensaje -->
                    <p v-else-if="field.status === 'pending'" class="text-xs text-gray-400">
                        El administrador revisará tu campo en las próximas 24 h.
                    </p>
                </div>
            </div>
        </div>

    </div>
</template>
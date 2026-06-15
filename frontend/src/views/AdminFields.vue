<script setup>
import { RefreshCw } from 'lucide-vue-next'
import { useAdminPendingSectors } from '../composables/useAdminPendingSectors'
import PendingFieldCard from '../components/admin/PendingFieldCard.vue'
import PolygonEditorModal from '../components/admin/PolygonEditorModal.vue'

const {
  fields, loading, error,
  editingSector, polygonGeoJSON, savingSector, sectorError, savedSectorIds,
  approvingId, approveError,
  loadPending, openSectorEditor, closeSectorEditor, saveSectorPolygon, confirmApproval,
} = useAdminPendingSectors()
</script>

<template>
  <div class="max-w-2xl lg:max-w-5xl mx-auto px-4 py-6">
    
    <div class="flex items-center justify-between mb-5">
        <h1 class="text-xl font-bold text-gray-900">Sectores pendientes</h1>
        <button @click="loadPending"
            class="flex items-center gap-1.5 border-2 border-gray-200 text-gray-600 font-semibold text-sm px-3 py-2 rounded-xl hover:border-gray-300 transition-colors">
            <RefreshCw class="w-3.5 h-3.5" />
            Recargar
        </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-400 text-sm">Cargando...</div>
    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-3 py-2.5 rounded-xl">
        {{ error }}
    </div>
    <div v-else-if="fields.length === 0" class="text-center py-12 text-gray-400 text-sm">No hay sectores pendientes.</div>

    <div v-else class="space-y-4">
        <PendingFieldCard
            v-for="field in fields"
            :key="field.id"
            :field="field"
            :saved-ids="savedSectorIds"
            :approving-id="approvingId"
            :approve-error="approveError"
            @edit="openSectorEditor"
            @approve="confirmApproval"
        />
    </div>

    <PolygonEditorModal
        v-if="editingSector"
        :sector="editingSector"
        v-model="polygonGeoJSON"
        :saving="savingSector"
        :error="sectorError"
        @close="closeSectorEditor"
        @save="saveSectorPolygon"
    />
  </div>
</template>
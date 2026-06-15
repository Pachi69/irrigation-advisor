import { ref, onMounted } from 'vue'
import { listPendingSectors, approveSector, adminUpdateSector } from '../services/admin'

export function useAdminPendingSectors() {
    const fields = ref([])
    const loading = ref(true)
    const error = ref('')

    const editingSector = ref(null)
    const polygonGeoJSON = ref(null)
    const savingSector = ref(false)
    const sectorError = ref('')
    const savedSectorIds = ref(new Set())

    const approvingId = ref(null)
    const approveError = ref('')

    async function loadPending() {
        error.value = ''
        loading.value = true
        try {
            fields.value = await listPendingSectors()
        } catch (err) {
            error.value = 'No se pudieron cargar los sectores. Intente nuevamente.'
        } finally {
            loading.value = false
        }
    }

    function openSectorEditor(sector) {
        editingSector.value = sector
        polygonGeoJSON.value = sector.polygon_geojson || null
        sectorError.value = ''
    }

    function closeSectorEditor() {
        editingSector.value = null
    }

    async function saveSectorPolygon() {
        if (!editingSector.value || !polygonGeoJSON.value) return
        savingSector.value = true
        sectorError.value = ''
        try {
            const updated = await adminUpdateSector(editingSector.value.id, {
                polygon_geojson: polygonGeoJSON.value,
            })
            for (const f of fields.value) {
                const idx = (f.sectors || []).findIndex(s => s.id === updated.id)
                if (idx !== -1) f.sectors[idx] = updated
            }
            savedSectorIds.value.add(updated.id)
            closeSectorEditor()
        } catch (err) {
            sectorError.value = err.response?.data?.detail || 'No se pudo guardar el poligono'
        } finally {
            savingSector.value = false
        }
    }

    async function confirmApproval(sector) {
        approvingId.value = sector.id
        approveError.value = ''
        try {
            const updated = await approveSector(sector.id)
            for (const f of fields.value) {
                const idx = (f.sectors || []).findIndex(s => s.id === updated.id)
                if (idx !== -1) f.sectors[idx] = updated
            }
            // Si el campo ya no tiene sectores pendientes, lo saca de la lista
            fields.value = fields.value.filter(f => (f.sectors || []).some(s => s.status === 'pending'))
        } catch (err) {
            approveError.value = err.response?.data?.detail || err.message || 'Error al aprobar el sector'
        } finally {
            approvingId.value = null
        }
    }

    onMounted(loadPending)

    return {
        fields, loading, error,
        editingSector, polygonGeoJSON, savingSector, sectorError, savedSectorIds,
        approvingId, approveError,
        loadPending, openSectorEditor, closeSectorEditor, saveSectorPolygon, confirmApproval,
    }
}
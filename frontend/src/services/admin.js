import api from './api'

export async function listPendingSectors() {
    // GET /admin/sectors/pending -> campos que tienen al menos un sector pendiente
    const { data } = await api.get('/admin/sectors/pending')
    return data
}

export async function approveSector(sectorId) {
    const { data } = await api.post(`/admin/sectors/${sectorId}/approve`)
    return data
}

export async function adminUpdateSector(sectorId, payload) {
    const { data } = await api.patch(`/admin/sectors/${sectorId}`, payload)
    return data
}
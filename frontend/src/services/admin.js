import api from './api'

export async function listPendingFields() {
    // GET /admin/fields/pending -> lista de campos con su dueño
    const { data } = await api.get('/admin/fields/pending')
    return data
}

export async function approveField(fieldId) {
    const { data } = await api.post(`/admin/fields/${fieldId}/approve`)
    return data
}

export async function adminUpdateSector(sectorId, payload) {
    const { data } = await api.patch(`/admin/sectors/${sectorId}`, payload)
    return data
}
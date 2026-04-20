import api from './api'

export async function listPendingFields() {
    // GET /admin/fields/pending -> lista de campos con su dueño
    const { data } = await api.get('/admin/fields/pending')
    return data
}

export async function approveField(fieldId, polygonGeojson) {
    // POST /admin/fields/:id/approve -> devuelve el campo actualizado
    const { data } = await api.post(`/admin/fields/${fieldId}/approve`, {
        polygon_geojson: polygonGeojson,
    })
    return data
}
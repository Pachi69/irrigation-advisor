import api from './api'

export async function createField(payload) {
    const { data } = await api.post('/fields', payload)
    return data
}

export async function listMyFields() {
    const { data } = await api.get('/fields')
    return data
}

export async function getFieldById(id) {
    const { data } = await api.get(`/fields/${id}`)
    return data
}

export async function getRecommendation(fieldId) {
    const { data } = await api.get(`/fields/${fieldId}/recommendation`)
    return data
}

export async function getFieldAlerts(fieldId) {
    const { data } = await api.get(`/fields/${fieldId}/alerts`)
    return data
}

export async function getRecommendationHistory(fieldId) {
    const { data } = await api.get(`/fields/${fieldId}/recommendations`)
    return data
}

export async function updateField(fieldId, payload) {
    const { data } = await api.patch(`/fields/${fieldId}`, payload)
    return data
}

export async function getFieldChartData(fieldId) {
    const { data } = await api.get(`/fields/${fieldId}/chart`)
    return data
}

export async function getFieldSatelliteImage(fieldId) {
    const resp = await api.get(`/fields/${fieldId}/satellite-image`, { responseType: 'blob' })
    return resp.data
}

export async function deleteField(fieldId) {
    await api.delete(`/fields/${fieldId}`)
}

export async function getPendingConfirmations(fieldId) {
    const { data } = await api.get(`/fields/${fieldId}/pending-confirmations`)
    return data
}

export async function confirmIrrigation(fieldId, recommendationId, payload) {
    const { data } = await api.post(`/fields/${fieldId}/recommendations/${recommendationId}/confirm`, payload,)
    return data
}
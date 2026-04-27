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
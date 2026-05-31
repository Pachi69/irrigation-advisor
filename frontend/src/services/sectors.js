import api from './api'


export async function createSector(fieldId, payload) {
    const { data } = await api.post(`/fields/${fieldId}/sectors`, payload)
    return data
}

export async function listFieldSectors(fieldId) {
    const { data } = await api.get(`/fields/${fieldId}/sectors`)
    return data
}

export async function getSectorById(sectorId) {
    const { data } = await api.get(`/sectors/${sectorId}`)
    return data
}

export async function updateSector(sectorId, payload) {
    const { data } = await api.patch(`/sectors/${sectorId}`, payload)
    return data
}

export async function deleteSector(sectorId) {
    await api.delete(`/sectors/${sectorId}`)
}


export async function getRecommendation(sectorId) {
    const { data } = await api.get(`/sectors/${sectorId}/recommendation`)
    return data
}

export async function getRecommendationHistory(sectorId) {
    const { data } = await api.get(`/sectors/${sectorId}/recommendations`)
    return data
}

export async function getSectorChartData(sectorId) {
    const { data } = await api.get(`/sectors/${sectorId}/chart`)
    return data
}

export async function getSectorSatelliteImage(sectorId) {
    const resp = await api.get(`/sectors/${sectorId}/satellite-image`, { responseType: 'blob' })
    return resp.data
}

export async function getPendingConfirmations(sectorId) {
    const { data } = await api.get(`/sectors/${sectorId}/pending-confirmations`)
    return data
}

export async function confirmIrrigation(sectorId, recommendationId, payload) {
    const { data } = await api.post(`/sectors/${sectorId}/recommendations/${recommendationId}/confirm`, payload,)
    return data
}
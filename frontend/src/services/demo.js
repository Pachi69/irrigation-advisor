import api from './api'

export async function getDemoSnapshot({ refresh = false } = {}) {
    const { data } = await api.get('/demo/snapshot', {
        params: refresh ? { refresh: true } : {},
    })
    return data
}

export async function getDemoSatelliteImage() {
    const resp = await api.get('/demo/satellite-image', { responseType: 'blob' })
    return resp.data
}
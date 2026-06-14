import { ref, computed, onBeforeUnmount } from 'vue'
import { getRecommendation, getSectorById, getRecommendationHistory, getSectorSatelliteImage, } from '../services/sectors'
import { getFieldAlerts } from '../services/fields'

export function useSectorRecommendation(sectorId) {
    const rec = ref(null)
    const sector = ref(null)
    const alerts = ref([])
    const loading = ref(true)
    const error = ref('')
    const satelliteUrl = ref(null)

    // timeline
    const dates= ref([])
    const selectedIndex = ref(false)
    const loadingDate = ref(false)
    const isLatest = computed(() => selectedIndex.value === dates.value.length - 1)
    const selectedDate = computed(() => dates.value[selectedIndex.value] || null)

    const dismissed = JSON.parse(localStorage.getItem('dismissedAlerts') || '[]')

    function setSatellite(url) {
        if (satelliteUrl.value) URL.revokeObjectURL(satelliteUrl.value)
        satelliteUrl.value = url
    }

    async function fetchSatelliteUrl(ndviDate) {
        if(!ndviDate) return null
        try {
            const blob = await getSectorSatelliteImage(sectorId, ndviDate)
            return URL.createObjectURL(blob)
        } catch {
            return null
        }
    }

    async function loadHistory() {
        try {
            const items = await getRecommendationHistory(sectorId)
            dates.value = items.map(i => i.date).reverse()
            selectedIndex.value = dates.value.length - 1
        } catch {}
    }

    async function fetchAlerts() {
        if (!sector.value?.field_id) return
        try {
            const all = await getFieldAlerts(sector.value.field_id)
            alerts.value = all.filter(a => !dismissed.includes(a.id))
        } catch {}
    }

    function dismissAlert(id) {
        dismissed.push(id)
        localStorage.setItem('dismissedAlerts', JSON.stringify(dismissed))
        alerts.value = alerts.value.filter(a => a.id !== id)
    }

    async function load() {
        try {
            [rec.value, sector.value] = await Promise.all([
                getRecommendation(sectorId),
                getSectorById(sectorId),
            ])
            await loadHistory()
            setSatellite(await fetchSatelliteUrl(rec.value.ndvi_date))
            fetchAlerts()
        } catch (e) {
            error.value = e?.response?.data?.detail || 'No se pudo obtener la recomendación'
        } finally {
            loading.value = false
        }
    }

    async function loadDate() {
        const d = dates.value[selectedIndex.value]
        if (!d) return
        loadingDate.value = true
        try {
            const newRec = await getRecommendation(sectorId, isLatest.value? undefined: d)
            const newUrl = await fetchSatelliteUrl(newRec.ndvi_date)
            rec.value = newRec
            setSatellite(newUrl)
        } catch (e) {
            error.value = e?.response?.data?.detail || 'No se pudo cargar esa fecha'
        } finally {
            loadingDate.value = false
        }
    }

    function stepDate(delta) {
        if (loadingDate.value) return
        const next = selectedIndex.value + delta
        if (next < 0 || next > dates.value.length - 1) return
        selectedIndex.value = next
        loadDate()
    }

    onBeforeUnmount(() => {
        if (satelliteUrl.value) URL.revokeObjectURL(satelliteUrl.value)
    })

    return {
        rec, sector, alerts, loading, error, satelliteUrl, dates, selectedIndex, loadingDate,
        isLatest, selectedDate, load, loadDate, stepDate, dismissAlert,
    }
}
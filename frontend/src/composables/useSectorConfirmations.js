import { ref, computed, onMounted } from 'vue'
import { getPendingConfirmations, confirmIrrigation, getSectorById } from '../services/sectors'
import { formatMinutes } from '../utils/format'

export function useSectorConfirmations(sectorId) {
    const items = ref([])
    const sector = ref(null)
    const loading = ref(true)
    const error = ref('')

    const selected = ref(null)
    const form = ref({ irrigation_date: '', hours: 0, minutes: 0, volume_m3: null })
    const submitting = ref(false)
    const formError = ref('')

    const today = new Date().toISOString().slice(0, 10)

    const hasCaudal = computed(() => sector.value?.flow_rate_ls_ha != null)
    const recLabel = computed(() => (hasCaudal.value ? 'Tiempo recomendado' : 'Volumen recomendado'))

    function recValue(item) {
        if (hasCaudal.value) return formatMinutes(item.time_min)
        return item.volume_m3 != null ? `${Math.round(item.volume_m3)} m³` : '—'
    }

    async function load() {
        loading.value = true
        error.value = ''
        try {
            [items.value, sector.value] = await Promise.all([
                getPendingConfirmations(sectorId),
                getSectorById(sectorId),
            ])
        } catch {
            error.value = 'No se pudieron cargar las recomendaciones pendientes'
        } finally {
            loading.value = false
        }
    }

    function openConfirm(item) {
        selected.value = item
        // Precarga el tiempo recomendado (h/min) o el volumen recomendado en m³
        const total = Math.round(item.time_min || 0)
        form.value = {
            irrigation_date: item.date,
            hours: Math.floor(total / 60),
            minutes: total % 60,
            volume_m3: hasCaudal.value ? null : (item.volume_m3 != null ? Math.round(item.volume_m3) : null),
        }
        formError.value = ''
    }

    function closeConfirm() {
        selected.value = null
    }

    async function submit() {
        formError.value = ''
        if (!form.value.irrigation_date) {
            formError.value = 'Elegí la fecha de riego'
            return
        }
        if (form.value.irrigation_date > today) {
            formError.value = 'La fecha de riego no puede ser futura'
            return
        }

        const payload = { irrigation_date: form.value.irrigation_date }

        if (hasCaudal.value) {
            const totalMin = (Number(form.value.hours) || 0) * 60 + (Number(form.value.minutes) || 0)
            if (!(totalMin > 0)) {
                formError.value = 'Ingresá un tiempo de riego mayor a 0 min'
                return
            }
            payload.applied_time_min = totalMin
        } else {
            const vol = Number(form.value.volume_m3)
            if (!(vol > 0)) {
                formError.value = 'Ingresá un volumen de riego mayor a 0 m3'
                return
            }
            payload.applied_volume_m3 = vol
        }

        submitting.value = true
        try {
            await confirmIrrigation(sectorId, selected.value.recommendation_id, payload)
            items.value = items.value.filter(
                (i) => i.recommendation_id !== selected.value.recommendation_id,
            )
            closeConfirm()
        } catch (e) {
            formError.value = e?.response?.data?.detail || 'No se pudo confirmar el riego'
        } finally {
            submitting.value = false
        }
    }

    onMounted(load)

    return {
        items, sector, loading, error, selected, form, submitting, formError,
        today, hasCaudal, recLabel, recValue,
        load, openConfirm, closeConfirm, submit,
    }
}

import { ref, computed, onMounted } from 'vue'
import { listMyFields } from '../services/fields'

export function useHomeDashboard() {
    const fields = ref([])
    const loading = ref(true)

    const todayLabel = computed(() => {
        const d = new Date()
        const day = d.toLocaleDateString('es-AR', { weekday: 'short' })
        const date = d.toLocaleDateString('es-AR', { day: 'numeric', month: 'long' })
        return `${day.replace('.', '')} · ${date} · San Rafael`
    })

    const activeFields = computed(() =>
        fields.value.filter(f => (f.sectors || []).some(s => s.status === 'active'))
    )

    // Sectores activos de todos los campos, con el nombre del campo embebido
    const activeSectors = computed(() =>
        fields.value.flatMap(f =>
            (f.sectors || [])
                .filter(s => s.status === 'active')
                .map(s => ({ ...s, fieldName: f.name }))
        )
    )

    const totalArea = computed(() =>
        activeSectors.value.reduce((s, sec) => s + (sec.area_ha || 0), 0).toFixed(1)
    )

    // Sector más urgente que necesita riego hoy
    const urgentSector = computed(() => {
        const withRec = activeSectors.value.filter(
            s => s.last_recommendation && ['high', 'critical'].includes(s.last_recommendation.urgency)
        )
        return withRec.sort((a, b) =>
            b.last_recommendation.recommended_irrigation_mm - a.last_recommendation.recommended_irrigation_mm
        )[0] || null
    })

    const urgentCount = computed(() => activeSectors.value.filter(
        s => s.last_recommendation && ['high', 'critical', 'medium'].includes(s.last_recommendation.urgency)
    ).length)

    async function load() {
        try {
            fields.value = await listMyFields()
        } finally {
            loading.value = false
        }
    }

    onMounted(load)

    return { fields, loading, todayLabel, activeFields, activeSectors, totalArea, urgentSector, urgentCount, load }
}
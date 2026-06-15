import { ref, computed, onMounted } from 'vue'
import { getSectorMetrics, getSectorById } from '../services/sectors'

const RANGES = [30, 60, 90]

export function useSectorMetrics(sectorId) {
    const days = ref(90)
    const data = ref(null)
    const sector = ref(null)
    const loading = ref(true)
    const error = ref('')

    const verdict = computed(() => {
        if (!data.value) return null
        const coverage = data.value.stress.demand_coverage_pct
        return {
            coverage: coverage != null ? Math.round(coverage) : null,
            ks: data.value.stress.avg_ks,
            perc: data.value.water.deep_percolation_mm,
            stressDays: data.value.stress.stress_days,
            days: data.value.stress.days_evaluated,
        }
    })

    const urgencyBar = computed(() => {
        if (!data.value) return []
        const u = data.value.urgency
        const total = u.low + u.medium + u.high + u.critical || 1
        return ['low', 'medium', 'high', 'critical']
            .map((key) => ({ key, n: u[key] }))
            .filter((x) => x.n > 0)
            .map((x) => ({ ...x, w: (x.n / total) * 100 }))
    })

    async function load() {
        loading.value = true
        error.value = ''
        try {
            data.value = await getSectorMetrics(sectorId, { days: days.value })
        } catch {
            error.value = 'No se pudieron cargar las metricas'
        } finally {
            loading.value = false
        }
    }

    function setRange(d) {
        if (d === days.value) return
        days.value = d
        load()
    }

    onMounted(async () => {
        try { sector.value = await getSectorById(sectorId) } catch {}
        await load()
    })

    return { RANGES, days, data, sector, loading, error, verdict, urgencyBar, load, setRange}
}
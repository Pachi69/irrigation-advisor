/**
 * Formatea minutos a un texto legible: "2 h 30 min", "45 min", "3 h".
 */
export function formatMinutes(totalMin) {
    if (totalMin == null) return '—'
    const mins = Math.round(totalMin)
    if (mins < 60) return `${mins} min`
    const h = Math.floor(mins / 60)
    const m = mins % 60
    return m === 0 ? `${h} h` : `${h} h ${m} min`
}

// Helpers de formato numerico para metricas (- si es null)
export const n0 = (v) => (v == null ? '—' : Math.round(v).toLocaleString('es-AR'))
export const n1 = (v) => (v == null ? '—' : v.toFixed(1))
export const n2 = (v) => (v == null ? '—' : v.toFixed(2))
export const pct = (v) => (v == null ? '—' : `${v.toFixed(1)}%`)

// Etiqueta corta de semana: "05 may"
export const fmtWeek = (ws) =>
    new Date(ws + 'T00:00:00').toLocaleDateString('es-AR', { day: '2-digit', month: 'short' })

// Cantidad de riego de una recomendacion. Lista para mostrar: tiempo, volumen o mm
export function irrigationAmount(rec) {
    if (rec.time_min != null) return formatMinutes(rec.time_min)
    if (rec.volume_m3 != null) return `${Math.round(rec.volume_m3)} m³`
    return `${rec.recommended_irrigation_mm.toFixed(1)} mm`
}
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
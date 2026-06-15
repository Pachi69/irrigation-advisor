export function useSectorForm() {
    const notifHours = Array.from({ length: 18 }, (_, i) => i + 5) //05:00 a 22:00
    const todayStr = new Date().toISOString().slice(0, 10)
    
    // Cadenas vacias -> null para los campos opcionales
    function normalizePayload(form) {
        return {
            ...form,
            variety: form.variety || null,
            flow_rate_ls_ha: form.flow_rate_ls_ha || null,
        }
    }
    
    return { notifHours, todayStr, normalizePayload }
}
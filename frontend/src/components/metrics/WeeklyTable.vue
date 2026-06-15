<script setup>
import { n1, n2, fmtWeek } from '../../utils/format'

defineProps({
    weekly: { type: Array, default: () => [] },
})
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3">Detalle semanal</div>

        <!-- desktop -->
        <div class="hidden md:block overflow-x-auto">
            <table class="w-full text-sm">
                <thead>
                    <tr>
                        <th class="app-label pb-2 text-left">Semana</th>
                        <th class="app-label pb-2 text-right">ETc</th>
                        <th class="app-label pb-2 text-right">Lluvia ef.</th>
                        <th class="app-label pb-2 text-right">Consumo neto</th>
                        <th class="app-label pb-2 text-right">Aplicada</th>
                        <th class="app-label pb-2 text-right">Percolación</th>
                        <th class="app-label pb-2 text-right">Ks</th>
                        <th class="app-label pb-2 text-right">Estrés</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="w in weekly" :key="w.week_start" class="border-t border-line">
                        <td class="py-2 text-muted">{{ fmtWeek(w.week_start) }}</td>
                        <td class="py-2 text-right app-mono">{{ n1(w.etc_mm) }}</td>
                        <td class="py-2 text-right app-mono text-water">{{ n1(w.effective_rain_mm) }}</td>
                        <td class="py-2 text-right app-mono font-bold">{{ n1(w.net_requirement_mm) }}</td>
                        <td class="py-2 text-right app-mono">{{ n1(w.applied_mm) }}</td>
                        <td class="py-2 text-right app-mono text-rust">{{ n1(w.deep_percolation_mm) }}</td>
                        <td class="py-2 text-right app-mono">{{ n2(w.avg_ks) }}</td>
                        <td class="py-2 text-right app-mono">{{ w.stress_days }}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- mobile -->
        <div class="md:hidden flex flex-col gap-2.5">
            <div v-for="w in weekly" :key="w.week_start" class="border border-line rounded-2xl px-3.5 py-3">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-bold text-ink">{{ fmtWeek(w.week_start) }}</span>
                    <span class="app-mono text-xs text-muted">Ks {{ n2(w.avg_ks) }} · {{ w.stress_days }}d estrés</span>
                </div>
                <div class="grid grid-cols-3 gap-2 text-center">
                    <div>
                        <div class="app-label">Consumo</div>
                        <div class="app-mono text-sm font-bold">{{ n1(w.net_requirement_mm) }}</div>
                    </div>
                    <div>
                        <div class="app-label">Aplicada</div>
                        <div class="app-mono text-sm font-bold">{{ n1(w.applied_mm) }}</div>
                    </div>
                    <div>
                        <div class="app-label">Percolación</div>
                        <div class="app-mono text-sm font-bold text-rust">{{ n1(w.deep_percolation_mm) }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
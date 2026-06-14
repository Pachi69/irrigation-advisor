<script setup>
defineProps({ rec: { type: Object, required: true } })
</script>

<template>
    <div class="bg-surface border border-line rounded-3xl p-5">
        <div class="app-label mb-3">Clima del día</div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
            <div>
                <div class="app-label">Temperatura</div>
                <div class="app-mono text-base font-bold mt-0.5">
                    {{ rec.temp_mean_c?.toFixed(1) }} <span class="text-sm text-muted font-semibold">°C</span>
                </div>
                <div class="text-xs text-muted mt-0.5">{{ rec.temp_min_c?.toFixed(0) }}° min / {{ rec.temp_max_c?.toFixed(0) }}° max</div>
            </div>
            <div>
                <div class="app-label">Humedad</div>
                <div class="app-mono text-base font-bold mt-0.5">
                    {{ rec.humidity_pct?.toFixed(0) }} <span class="text-sm text-muted font-semibold">%</span>
                </div>
            </div>
            <div>
                <div class="app-label">Lluvia</div>
                <div class="app-mono text-base font-bold mt-0.5">
                    {{ rec.precipitation_mm?.toFixed(1) }} <span class="text-sm text-muted font-semibold">mm</span>
                </div>
            </div>
            <div>
                <div class="app-label">Viento</div>
                <div class="app-mono text-base font-bold mt-0.5">
                    {{ rec.wind_speed_ms != null ? (rec.wind_speed_ms * 3.6).toFixed(1) : '-' }} <span class="text-sm text-muted font-semibold">km/h</span>
                </div>
            </div>
            <div>
                <div class="app-label">Radiación solar</div>
                <div class="app-mono text-base font-bold mt-0.5">
                    {{ rec.solar_radiation_mj?.toFixed(1) }} <span class="text-sm text-muted font-semibold">MJ/m²</span>
                </div>
            </div>
            <div>
                <div class="app-label">Presión atmosférica</div>
                <div class="app-mono text-base font-bold mt-0.5">
                    {{ Math.round(rec.pressure_kpa * 10) }} <span class="text-sm text-muted font-semibold">hPa</span>
                </div>
            </div>
        </div>
        <p class="text-xs text-muted mt-3 leading-relaxed">
            Variables de Open-Meteo para la fecha de la recomendación: alimentan el ETo y la lluvia el balance hidrico.
        </p>
    </div>
</template>
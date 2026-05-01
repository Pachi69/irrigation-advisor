<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import '@geoman-io/leaflet-geoman-free'
import 'leaflet/dist/leaflet.css'
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css'

const props = defineProps({
    modelValue: { type: Object, default: null},
    height: { type: String, default: '380px'},
})
const emit = defineEmits(['update:modelValue'])

const mapRef = ref(null)
let map = null
let activeLayer = null

function emitCurrent() {
    emit('update:modelValue', activeLayer ? activeLayer.toGeoJSON().geometry : null)
}

onMounted(() => {
    map = L.map(mapRef.value).setView([-34.617, -68.330], 13)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
    }).addTo(map)

    map.pm.addControls({
        position: 'topleft',
        drawMarker: false,
        drawCircleMarker: false,
        drawPolyline: false,
        drawRectangle: false,
        drawPolygon: true,
        drawCircle: false,
        editMode: true,
        dragMode: false,
        cutPolygon: false,
        removalMode: true,
        drawText: false,
        rotateMode: false
    })

    // Mosrtar poligono existente (modo edicion)
    if (props.modelValue) {
        const geoLayer = L.geoJSON(props.modelValue)
        activeLayer = geoLayer.getLayers()[0]
        if (activeLayer) {
            activeLayer.addTo(map)
            map.fitBounds(activeLayer.getBounds(), { padding: [30, 30]})
        }
    }

    map.on('pm:create', ({ layer }) => {
        if (activeLayer) map.removeLayer(activeLayer)
        activeLayer = layer
        emitCurrent()
    })

    map.on('pm:edit', () => emitCurrent())

    map.on('pm:remove', ({ layer }) => {
        if (activeLayer === layer) activeLayer = null
        emitCurrent()
    })
})

onBeforeUnmount(() => {
    map?.remove()
    map = null
})
</script>
<template>
    <div ref="mapRef" class="map-editor" />
</template>

<style scoped>
.map-editor {
    width: 100%;
    height: v-bind(height);
    border-radius: 6px;
    border: 1px solid #ccc;
    position: relative;
}
</style>
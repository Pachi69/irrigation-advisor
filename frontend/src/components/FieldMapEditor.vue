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

    const satelite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Imagery © <a href="https://www.esri.com/">Esri</a>',
        maxZoom: 20,
        maxNativeZoom: 17,
    })
    const terreno = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 20,
        maxNativeZoom: 19,
    })
    const rutas = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 20,
        maxNativeZoom: 16,
    })

    satelite.addTo(map)
    rutas.addTo(map)

    L.control.layers(
        { 'Satélite': satelite, 'Terreno': terreno },
        { 'Rutas y calles': rutas },
    ).addTo(map)

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
            attachLayerListeners(activeLayer)
        }
    }

    function attachLayerListeners(layer) {
        layer.on('pm:markerdragend', emitCurrent)
        layer.on('pm:vertexadded', emitCurrent)
        layer.on('pm:vertexremoved', emitCurrent)
    }

    map.on('pm:create', ({ layer }) => {
        if (activeLayer) map.removeLayer(activeLayer)
        activeLayer = layer
        attachLayerListeners(layer)
        emitCurrent()
    })

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
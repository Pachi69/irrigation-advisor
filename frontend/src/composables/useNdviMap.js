import { ref, watch, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const TILE_URL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'

export function useNdviMap(mapRef, sector, satelliteUrl) {
    const overlayOpacity = ref(0.8)
    let map = null
    let overlayLayer = null
    let bounds = null

    watch([sector, mapRef], ([s, el]) => {
        if (!s?.polygon_geojson || !el || map) return
        const coords = s.polygon_geojson.coordinates[0]
        const lats = coords.map(c => c[1])
        const lngs = coords.map(c => c[0])
        bounds = [[Math.min(...lats), Math.min(...lngs)], [Math.max(...lats), Math.max(...lngs)]]
        map = L.map(el, { zoomControl: false, attributionControl: false })
        L.tileLayer(TILE_URL).addTo(map)
        L.polygon(coords.map(c => [c[1], c[0]]), { color: 'white', weight: 2, fill: false }).addTo(map)
        if (satelliteUrl.value) overlayLayer = L.imageOverlay(satelliteUrl.value, bounds, { opacity: overlayOpacity.value }).addTo(map)
        map.fitBounds(bounds, { padding: [10, 10] })
        setTimeout(() => map?.invalidateSize(), 100)
    }, { flush: 'post' })

    watch(satelliteUrl, (url) => {

        if (!map || !bounds) return
        if (url) {
            if (overlayLayer) overlayLayer.setUrl(url)
            else overlayLayer = L.imageOverlay(url, bounds, { opacity: overlayOpacity.value }).addTo(map)
        } else if (overlayLayer) {
            map.removeLayer(overlayLayer)
            overlayLayer = null
        }
    }, { flush: 'post' })

    watch(overlayOpacity, v => overlayLayer?.setOpacity(v))

    onBeforeUnmount(() => {
        map?.remove(); map = null; overlayLayer = null
    })

    return { overlayOpacity }
}
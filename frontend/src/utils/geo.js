/**
 * Replica la lógica de backend/app/api/_geo.py para mostrar un preview del centroide.
 * La validación real la sigue haciendo el backend al enviar.
 */

export function computeCentroidPreview(geojson) {
    if (!geojson || typeof geojson !== 'object') {
        throw new Error('El polígono debe ser un objeto GeoJSON')
    }

    // Soporta Feature o Geometry directa
    const geometry = geojson.type === 'Feature' ? geojson.geometry : geojson
    if (!geometry || typeof geometry !== 'object') {
        throw new Error('El feature no tiene una geometria valida')
    }

    const { type, coordinates} = geometry
    if (type !== 'Polygon' && type !== 'MultiPolygon') {
        throw new Error(`Tipo de geometria no soportada: ${type}. Solo se permiten Polygon y MultiPolygon.`)
    }

    if (!Array.isArray(coordinates) || coordinates.length === 0) {
        throw new Error('Las coordenadas estan vacias o no son una lista')
    }

    // Aplanamos vértices del anillo exterior (o de todos los exteriores en MultiPolygon)
    const points = type === 'Polygon'
        ? coordinates[0]
        : coordinates.flatMap((polygon) => polygon[0])

    if (!points || points.length === 0) {
        throw new Error('El poligono no tiene vertices')
    }

    // Sacamos el cierre repetido si existe
    const first = points[0]
    const last = points[points.length - 1]
    const closed = Array.isArray(first) && Array.isArray(last)
        && first[0] === last[0] && first[1] === last[1]
    const unique = closed? points.slice(0, -1) : points

    if (unique.length < 3) {
        throw new Error(`Un poligono requiere al menos 3 vertices unicos, se recibieron ${unique.length}`)
    }

    // Validación de cada vértice
    for (let i = 0; i < unique.length; i++) {
        const pt = unique[i]
        if (!Array.isArray(pt) || pt.length < 2) {
            throw new Error(`El vertice ${i} no tiene formato [lon, lat]`)
        }
        const [lon, lat] = pt
        if (typeof lon !== 'number' || typeof lat !== 'number') {
            throw new Error(`El vertice ${i} tiene coordenadas no numericas`)
        }
        if (lon < -180 || lon > 180) {
            throw new Error(`El vertice ${i} tiene una longitud fuera del rango [-180, 180]`)
        }
        if (lat < -90 || lat > 90) {
            throw new Error(`El vertice ${i} tiene una latitud fuera del rango [-90, 90]`)
        }
    }

    const lonSum = unique.reduce((acc, pt) => acc + pt[0], 0)
    const latSum = unique.reduce((acc, pt) => acc + pt[1], 0)
    return {
        latitude: latSum / unique.length,
        longitude: lonSum / unique.length,
    }
}
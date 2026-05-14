"""Utilidades geometricas para procesamiento de poligonos GeoJSON"""
from typing import Any
import math


def validate_and_compute_centroid(geojson: dict[str, Any]) -> tuple[float, float]:
    """Valida un GeoJSON Feature/Geometry y devulve (latitude, longitude) del centroide.
    
    Soporta Polygon y MultiPolygon. Si es un Feature, extrae el geometry.
    Raises ValueError si el GeoJSON no es valido o no es un poligono.
    """
    if not isinstance(geojson, dict):
        raise ValueError("El poligono debe ser un objeto GeoJSON")
    
    # Si es un Feature, extraemos el geometry
    if geojson.get("type") == "Feature":
        geometry = geojson.get("geometry")
        if not isinstance(geometry,dict):
            raise ValueError("El Feature no tiene una geometry valida")
    else:
        geometry = geojson

    geom_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError(
            f"Tipo de geometria no soportada: {geom_type}. Solo se permiten Polygon y MultiPolygon."
        )
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("Las coordenadas estan vacias o no son una lista")
    
    #Aplanar una lista de puntos [lon, lat]
    try:
        if geom_type == "Polygon":
            # coordinates = [ring_exterior, ring_interior1, ...] usamos solo el exterior
            points = coordinates[0]  # Primer anillo es el exterior
        else:
            # Multypolygon: coordinates = [ [exterior, holes], [exterior, holes], ...]
            points = [pt for polygon in coordinates for pt in polygon[0]]  # Aplanar todos los exteriores

        if not points:
            raise ValueError("El poligono no tiene vertices.")

        # Centroide geometrico simple: promedio de vertices (excluyendo el cierre repetido)
        unique_points = points[:-1] if points[0] == points[-1] else points

        # Un polígono necesita al menos 3 vértices únicos para formar un área
        if len(unique_points) < 3:
            raise ValueError(
                f"Un polígono requiere al menos 3 vértices únicos, se recibieron {len(unique_points)}."
            )

        # Validar cada vértice individualmente: lon en [-180,180], lat en [-90,90]
        for idx, pt in enumerate(unique_points):
            if not isinstance(pt, list) or len(pt) < 2:
                raise ValueError(f"Vértice {idx} no tiene formato [lon, lat].")
            lon, lat = pt[0], pt[1]
            if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                raise ValueError(f"Vértice {idx} tiene coordenadas no numéricas.")
            if not (-180 <= lon <= 180):
                raise ValueError(
                    f"Vértice {idx}: longitud {lon} fuera de rango [-180, 180]."
                )
            if not (-90 <= lat <= 90):
                raise ValueError(
                    f"Vértice {idx}: latitud {lat} fuera de rango [-90, 90]."
                )

        lon_sum = sum(pt[0] for pt in unique_points)
        lat_sum = sum(pt[1] for pt in unique_points)
        n = len(unique_points)
        centroids_lon = lon_sum / n
        centroids_lat = lat_sum / n

    except (IndexError, TypeError, ZeroDivisionError) as e:
        raise ValueError(f"Estructura de coordenadas invalidas: {e}")

    return (centroids_lat, centroids_lon)


def compute_area_ha(geojson: dict[str, Any]) -> float:
    """Calcula el area en hectareas de un GeoJSON Polygon/MultiPolygon.
    
    Usa proyeccion equirectangular local centrada en el centroide del poligono.
    Adecuada para parcelas agricolas (<10km de extension): error <0.1%.
    Asume coordenadas WGS84 (lon, lat) en grados, Soporta hoyos (interior rings).

    Raises ValueError si el GeoJSON no es valido o no es un poligono
    """
    centroid_lat, centroid_lon = validate_and_compute_centroid(geojson)
    geometry = geojson["geometry"] if geojson.get("type") == "Feature" else geojson
    geom_type = geometry["type"]
    coordinates = geometry["coordinates"]

    M_PER_DEG = 111_320.0 # ~longitud de 1 grado de latitud en metros
    cos_lat = math.cos(math.radians(centroid_lat))

    def ring_area_m2(ring: list[list[float]]) -> float:
        n = len(ring)
        if n < 3:
            return 0.0
        xs = [(pt[0] - centroid_lon) * cos_lat * M_PER_DEG for pt in ring]
        ys = [(pt[1] - centroid_lat) * M_PER_DEG for pt in ring]
        area2 = 0.0
        for i in range(n):
            j = (i + 1) % n
            area2 += xs[i] * ys[j] - xs[j] * ys[i]
        return abs(area2) / 2.0
    
    total_m2 = 0.0
    if geom_type == "Polygon":
        rings = coordinates
        total_m2 = ring_area_m2(rings[0])
        for hole in rings[1:]:
            total_m2 -= ring_area_m2(hole)
    else: # Multipolygon
        for polygon in coordinates:
            total_m2 += ring_area_m2(polygon[0])
            for hole in polygon[1:]:
                total_m2 -= ring_area_m2(hole)
    
    return round(max(0.0, total_m2) / 10_000.0, 4)
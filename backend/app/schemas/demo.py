from datetime import date

from pydantic import BaseModel

from app.models.enums import ConfidenceLevel, KcSource, PhenologicalStage, UrgencyLevel


class DemoTrajectoryPoint(BaseModel):
    """Un dia de roll ancla -> objetivo (para el grafico de trayectoria)."""
    date: date
    deficit_mm: float
    deficit_pct: float
    etc_mm: float
    precipitation_mm: float
    kc: float
    kc_source: KcSource
    ndvi: float | None = None

class DemoSnapshot(BaseModel):
    """Resultado completo del pipeline corrido sobre la fecha de verano preset."""
    # Identidad del sector demo
    sector_name: str
    crop_type: str
    variety: str | None = None
    area_ha: float
    polygon_geojson: dict

    #Fechas del caso
    anchor_date: date
    target_date: date

    # Recomendacion / urgencia (en target_date)
    urgency_level: UrgencyLevel
    recommended_irrigation_mm: float
    volume_m3: float | None = None
    time_min: float | None = None
    reason: str
    confidence: ConfidenceLevel
    
    #Balance Hidrico
    water_deficit_mm: float
    ks: float
    taw_mm: float
    raw_mm: float

    #Evapotranspiracion / coeficiente de cultivo
    eto_mm: float
    etc_mm: float
    kc: float
    kc_source: KcSource
    phenological_stage: PhenologicalStage

    # Satelite (imagen de la fecha objetivo)
    ndvi: float | None = None
    ndvi_date: date | None = None
    cloud_cover_pct: float | None = None

    # Contraste con el estado ACTUAL (reposo invernal) del mismo sector:
    # Hoy el NDVI no se usa (Kc tabular); en verano si (Kc dinamico)
    current_kc: float
    current_kc_source: KcSource
    current_phenological_stage: PhenologicalStage

    # Trayectoria ancla -> objetivo
    trajectory: list[DemoTrajectoryPoint]

    # Nota de transparencia para la UI
    note: str
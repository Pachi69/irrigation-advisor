from datetime import date as DateType, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.models.field import Field as FieldModel
from app.schemas.climate import ClimateData, ForecastDay
from app.ingestion.climate import get_climate_data, get_forecast
from app.calculation.eto import calculate_eto
from app.api._helpers import located_field

router = APIRouter(prefix="/fields", tags=["climate"])


@router.get("/{field_id}/climate", response_model=ClimateData)
def get_field_climate(
    field: FieldModel = Depends(located_field),
    target_date: Optional[DateType] = Query(
        default=None,
        alias="date",
        description="Fecha YYYY-MM-DD (por defecto: ayer)",
    ),
):
    """Devuelve los datos climaticos de un dia para el campo indicado.
    
    - Por defecto consulta el dia de ayer.
    - Acepta fechas de hasta 92 dias atras.
    - El campo debe estar activo (poligono asignado por admin)"""
    resolved_date = target_date if target_date is not None else DateType.today() - timedelta(days=1)

    try:
        climate = get_climate_data(field.latitude, field.longitude, resolved_date)
        if climate.eto_reference_mm is None:
            eto_result = calculate_eto(climate, field.latitude, resolved_date, field.elevation_m)
            climate = climate.model_copy(update={"eto_reference_mm": eto_result.eto_mm})
        return climate
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    

@router.get("/{field_id}/forecast", response_model=list[ForecastDay])
def get_field_forecast(
    field: FieldModel = Depends(located_field),
    days: int = Query(default=5, ge= 1, le=16, description="Dias a pronosticar [1-16]"),
):
    """Devuelve el pronostico de los proximos N dias para el campo indicado.
    - Por defecto 5 dias.
    - El campo debe estar activo (poligono asignado por admin)
    """

    try:
        return get_forecast(field.latitude, field.longitude, days)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
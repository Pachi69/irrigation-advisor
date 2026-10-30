"""Ayudantes comunes de las pruebas de integración y de flujo completo.

La base es SQLite (ver `tests/__init__.py`) y se recrea en cada prueba con
`reset_database`. Las coordenadas y el polígono son ficticios.
"""
from datetime import date, time, timedelta

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Field, Sector, User, UserRole
from app.models.enums import CropType, IrrigationType, SectorStatus, SoilType
from app.schemas.climate import ClimateData, ForecastDay

LATITUDE = -10.0
LONGITUDE = -60.0
ELEVATION_M = 700.0
POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [LONGITUDE, LATITUDE],
        [LONGITUDE + 0.001, LATITUDE],
        [LONGITUDE + 0.001, LATITUDE + 0.001],
        [LONGITUDE, LATITUDE + 0.001],
        [LONGITUDE, LATITUDE],
    ]],
}


def reset_database() -> None:
    """Borra y vuelve a crear todas las tablas, solo sobre la base SQLite de prueba."""
    if engine.url.get_backend_name() != "sqlite":
        raise RuntimeError(
            "reset_database solo corre sobre la base SQLite de prueba: "
            "correr las pruebas con 'python -m unittest discover -s tests -t .'"
        )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def new_session() -> Session:
    return SessionLocal()


def make_user(db: Session, email: str = "productor@example.com", role: UserRole = UserRole.producer) -> User:
    user = User(name="Productor de prueba", email=email, password_hash="sin-uso", role=role)
    db.add(user)
    db.flush()
    return user


def make_field(db: Session, user: User, soil_type: SoilType | None = SoilType.loam) -> Field:
    field = Field(
        user_id=user.id, name="Campo de prueba", soil_type=soil_type,
        elevation_m=ELEVATION_M, latitude=LATITUDE, longitude=LONGITUDE,
    )
    db.add(field)
    db.flush()
    return field


def make_sector(
    db: Session,
    field: Field,
    name: str = "Sector de prueba",
    status: SectorStatus = SectorStatus.active,
    last_deficit_mm: float | None = None,
    last_deficit_date: date | None = None,
    notification_hour: time | None = None,
    notification_frequency_days: int = 1,
    last_notification_date: date | None = None,
) -> Sector:
    sector = Sector(
        field_id=field.id, name=name, crop_type=CropType.vine, area_ha=1.0,
        polygon_geojson=POLYGON, irrigation_type=IrrigationType.aspersion,
        flow_rate_ls_ha=10.0, status=status,
        last_deficit_mm=last_deficit_mm, last_deficit_date=last_deficit_date,
        notification_hour=notification_hour,
        notification_frequency_days=notification_frequency_days,
        last_notification_date=last_notification_date,
    )
    db.add(sector)
    db.flush()
    return sector


def climate_day(day: date, **overrides) -> ClimateData:
    """Día de verano seco con ETo de referencia de 6 mm."""
    values: dict = dict(
        date=day, temp_max_c=32.0, temp_min_c=16.0, temp_mean_c=24.0,
        humidity_pct=40.0, wind_speed_10m=2.0, solar_radiation_mj=26.0,
        precipitation_mm=0.0, pressure_kpa=93.0, eto_reference_mm=6.0,
    )
    values.update(overrides)
    return ClimateData(**values)


def climate_range(start: date, end: date) -> dict[date, ClimateData]:
    return {start + timedelta(days=i): climate_day(start + timedelta(days=i)) for i in range((end - start).days + 1)}


def forecast_days(start: date, days: int = 3, precipitation_mm: float = 0.0) -> list[ForecastDay]:
    return [
        ForecastDay(
            date=start + timedelta(days=i), temp_max_c=32.0, temp_min_c=16.0,
            precipitation_mm=precipitation_mm, precipitation_probability_pct=0.0,
            eto_reference_mm=6.0,
        )
        for i in range(days)
    ]

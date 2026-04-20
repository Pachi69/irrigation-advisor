from pydantic import BaseModel, Field

from app.schemas.field import FieldPublic
from app.schemas.auth import UserPublic

class FieldApproval(BaseModel):
    """Body del endpoint de aprobacion: solo el poligono GeoJSON"""
    polygon_geojson: dict = Field(
        description="Feature o Geometry GeoJSON del tipo Polygon o MultiPolygon"
    )

class FieldAdminView(FieldPublic):
    """Vista extendida del campo para el admin: incluye dueño."""
    user: UserPublic
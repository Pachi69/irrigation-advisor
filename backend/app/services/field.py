import logging

from sqlalchemy.orm import Session

from app.models.field import Field as FieldModel
from app.services.sector import initialize_sector_balance


logger = logging.getLogger(__name__)


def initialize_field_balance(field: FieldModel, db: Session) -> None:
    """Inicializa el balance hídrico de todos los sectores de un campo aprobado."""
    for sector in field.sectors:
        initialize_sector_balance(sector, db)
from pydantic import BaseModel

from app.schemas.field import FieldPublic
from app.schemas.auth import UserPublic

class FieldApproval(BaseModel):
    """Body de la aprobación. Los polígonos de los sectores se editan
    vía PATCH /sectors/{sector_id} antes de aprobar."""
    pass

class FieldAdminView(FieldPublic):
    """Vista extendida del campo para el admin: incluye dueño."""
    user: UserPublic
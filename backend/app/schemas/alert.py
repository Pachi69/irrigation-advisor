from datetime import date
from pydantic import BaseModel
from app.models.alert import AlertType

class AlertPublic(BaseModel):
    id: int
    type: AlertType
    message: str
    date: date

    model_config = {"from_attributes": True}
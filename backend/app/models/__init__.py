from app.models.user import User, UserRole
from app.models.field import Field, CropType, IrrigationType, SoilType, FieldStatus
from app.models.soil import Soil
from app.models.irrigation_confirmation import IrrigationConfirmation
from app.models.recommendation import Recommendation, KcSource, PhenologicalStage, UrgencyLevel, ConfidenceLevel
from app.models.alert import Alert, AlertType
from app.models.satellite_record import SatelliteRecord, SatelliteSource
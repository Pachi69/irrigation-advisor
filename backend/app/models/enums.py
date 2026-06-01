import enum

class KcSource(enum.Enum):
    s2_dynamic = "s2_dynamic"
    tabular = "tabular"

class PhenologicalStage(enum.Enum):
    initial = "initial"
    development = "development"
    mid = "mid"
    late = "late"
    dormancy = "dormancy"

class UrgencyLevel(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class ConfidenceLevel(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class CropType(enum.Enum):
    vine = "vine"
    peach = "peach"


class SoilType(enum.Enum):
    sand = "sand"
    loamy_sand = "loamy_sand"
    sandy_loam = "sandy_loam"
    sandy_clay_loam = "sandy_clay_loam"
    loam = "loam"
    silt_loam = "silt_loam"
    silt = "silt"
    clay_loam = "clay_loam"
    silty_clay_loam = "silty_clay_loam"
    sandy_clay = "sandy_clay"
    silty_clay = "silty_clay"
    clay = "clay"


class SectorStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"


class IrrigationType(enum.Enum):
    aspersion = "aspersion"
    superficial = "superficial"

class HailNetType(enum.Enum):
    none = "none"
    open = "open"
    dense = "dense"
    color = "color"
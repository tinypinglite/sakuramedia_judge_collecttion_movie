"""插件私有配置。"""

from pydantic import BaseModel, ConfigDict, Field


class DurationCollectionSettings(BaseModel):
    """按分钟配置合集判定阈值。"""

    model_config = ConfigDict(extra="forbid")

    duration_threshold_minutes: int = Field(default=300, ge=1)

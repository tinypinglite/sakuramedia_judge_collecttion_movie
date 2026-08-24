"""插件私有配置。"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_number_feature(value: str) -> str:
    return (value or "").strip().upper()


class DurationCollectionSettings(BaseModel):
    """按时长或番号特征配置合集判定规则。"""

    model_config = ConfigDict(extra="forbid")

    duration_threshold_minutes: int = Field(default=300, ge=1)
    number_features: set[str] = Field(
        default_factory=lambda: {"OFJE", "CJOB", "DVAJ", "REBD"}
    )

    @field_validator("number_features", mode="before")
    @classmethod
    def _normalize_number_features(cls, value) -> set[str]:
        if value is None:
            return set()
        return {
            normalized
            for item in value
            if (normalized := _normalize_number_feature(str(item)))
        }

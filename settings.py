"""插件私有配置。"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .translations import text_map


def _normalize_number_feature(value: str) -> str:
    return (value or "").strip().upper()


def _normalize_tag_name(value: str) -> str:
    return (value or "").strip().casefold()


class DurationCollectionSettings(BaseModel):
    """按时长、番号特征或标签配置合集判定规则。"""

    model_config = ConfigDict(extra="forbid")

    duration_threshold_minutes: int = Field(
        default=300,
        ge=1,
        title="合集时长阈值（分钟）",
        json_schema_extra={
            "title_i18n": text_map("settings.duration_threshold_minutes.title"),
        },
    )
    number_features: set[str] = Field(
        default_factory=lambda: {"OFJE", "CJOB", "DVAJ", "REBD"},
        title="番号前缀",
        json_schema_extra={
            "title_i18n": text_map("settings.number_features.title"),
        },
    )
    suffix_number_features: set[str] = Field(
        default_factory=set,
        title="番号后缀",
        json_schema_extra={
            "title_i18n": text_map("settings.suffix_number_features.title"),
        },
    )
    tag_names: set[str] = Field(
        default_factory=set,
        title="标签",
        json_schema_extra={
            "title_i18n": text_map("settings.tag_names.title"),
        },
    )

    @field_validator("number_features", "suffix_number_features", mode="before")
    @classmethod
    def _normalize_number_features(cls, value) -> set[str]:
        if value is None:
            return set()
        return {
            normalized
            for item in value
            if (normalized := _normalize_number_feature(str(item)))
        }

    @field_validator("tag_names", mode="before")
    @classmethod
    def _normalize_tag_names(cls, value) -> set[str]:
        if value is None:
            return set()
        return {
            normalized
            for item in value
            if (normalized := _normalize_tag_name(str(item)))
        }

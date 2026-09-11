"""SakuraMedia 按影片时长判定合集插件。"""

from .plugin import register
from .settings import DurationCollectionSettings

__all__ = ["DurationCollectionSettings", "register"]

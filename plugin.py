"""按影片时长批量判定合集影片。"""

from __future__ import annotations

from typing import Any

from src.plugins import HOST_API_VERSION, PluginContext, PluginRegistration
from src.scheduler.contracts import JobDefinition

from .settings import DurationCollectionSettings

PLUGIN_ID = "sakuramedia_judge_collecttion_movie"
DISPLAY_NAME = "按时长判定合集影片"
VERSION = "0.1.0"
PAGE_SIZE = 500


def judge_movies(
    context: PluginContext,
    config: DurationCollectionSettings,
    reporter: Any | None = None,
) -> dict[str, int]:
    """遍历全库并按 ``duration_minutes >= threshold`` 更新合集字段。"""
    logger = context.get_task_logger("judge-collection-by-duration")
    plugin_owner = f"plugin:{context.plugin_id}"
    after_id = 0
    stats = {
        "scanned": 0,
        "updated": 0,
        "unchanged": 0,
        "skipped_owned": 0,
        "patch_failed": 0,
    }

    while True:
        page = context.movies.list_page(after_id=after_id, limit=PAGE_SIZE)
        if not page.items:
            break

        for snapshot in page.items:
            stats["scanned"] += 1
            duration_minutes = snapshot.values.get("duration_minutes") or 0
            target_is_collection = duration_minutes >= config.duration_threshold_minutes
            if bool(snapshot.values["is_collection"]) == target_is_collection:
                stats["unchanged"] += 1
                continue

            owner = snapshot.owners.get("is_collection")
            if owner is not None and owner != plugin_owner:
                stats["skipped_owned"] += 1
                continue

            patched = context.movies.patch(
                snapshot.movie_id,
                {"is_collection": target_is_collection},
                expected_revision=snapshot.revision,
            )
            stats["updated" if patched else "patch_failed"] += 1

        if reporter is not None:
            reporter.progress_callback(
                {
                    "current": stats["scanned"],
                    "text": (
                        f"扫描 {stats['scanned']} 部，已更新 {stats['updated']} 部，"
                        f"跳过 owner {stats['skipped_owned']} 部"
                    ),
                }
            )

        if page.next_cursor is None:
            break
        after_id = page.next_cursor

    logger.info(
        "按时长判定合集完成 threshold={} stats={}",
        config.duration_threshold_minutes,
        stats,
    )
    return stats


def register(context: PluginContext) -> PluginRegistration:
    """声明定时判定任务；不在加载阶段访问影片库。"""
    config = DurationCollectionSettings.model_validate(dict(context.settings))

    def run_judgement(reporter, _params):
        return judge_movies(context, config, reporter)

    return PluginRegistration(
        plugin_id=PLUGIN_ID,
        display_name=DISPLAY_NAME,
        version=VERSION,
        host_api_version=HOST_API_VERSION,
        jobs=(
            JobDefinition(
                task_key="sakuramedia_judge_collecttion_movie",
                log_name="judge-collection-by-duration",
                cli_name="judge-collection-by-duration",
                cli_help="按影片时长判定合集影片",
                default_cron="0 4 * * *",
                handler=run_judgement,
            ),
        ),
    )

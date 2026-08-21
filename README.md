# SakuraMedia 按时长判定合集影片插件

遍历 SakuraMedia 全部影片，按 `duration_minutes` 判定是否为合集：

```text
duration_minutes >= duration_threshold_minutes  -> is_collection = true
duration_minutes <  duration_threshold_minutes  -> is_collection = false
```

默认阈值为 300 分钟，单位为分钟。配置示例：

```toml
[plugins.settings.sakuramedia_judge_collecttion_movie]
duration_threshold_minutes = 180
```

插件任务名为 `sakuramedia_judge_collecttion_movie`，默认每天凌晨 4 点执行，也可以通过
宿主的任务中心手动触发。

插件只在判定结果与当前值不一致时调用 `context.movies.patch()`。人工 owner
(`host:manual`) 或其他插件 owner 接管的影片会跳过，不会自动恢复或抢回主权。

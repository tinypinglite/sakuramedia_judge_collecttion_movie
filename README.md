# SakuraMedia 按时长判定合集影片插件

遍历 SakuraMedia 全部影片，按 `duration_minutes` 判定是否为合集：



默认阈值为 300 分钟，单位为分钟。在插件管理页（系统设置 → 插件）点击本插件行，按 JSON 编辑并保存：

```json
{
    "duration_threshold_minutes": 300
}
```

插件任务名为 `sakuramedia_judge_collecttion_movie`，默认每天凌晨 4 点执行，也可以通过
宿主的任务中心手动触发。

在APP内手动标记的合集和单体不会被此插件覆盖。

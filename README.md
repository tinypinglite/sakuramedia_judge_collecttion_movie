# SakuraMedia 合集影片判定插件

遍历 SakuraMedia 全部影片：时长达到 `duration_minutes` 阈值、番号以前缀特征开头、以后缀特征结尾，
或关联标签命中 `tag_names` 中任意一个时，标记为合集。未命中的影片不作任何写入，也不会取得
`is_collection` 的字段 owner。



默认阈值为 300 分钟，单位为分钟。在插件管理页（系统设置 → 插件）点击本插件行，通过配置表单编辑并保存。配置对象示例：

```json
{
    "duration_threshold_minutes": 300,
    "number_features": ["OFJE", "CJOB", "DVAJ", "REBD"],
    "suffix_number_features": [],
    "tag_names": []
}
```

`number_features` 为前缀列表，`suffix_number_features` 为后缀列表；两者都会忽略首尾空格和大小写。例如配置
`"suffix_number_features": ["-V"]` 时，`STAR-600-V` 会被判定为合集。

`tag_names` 为标签名列表（表单中每行一个），多个标签之间为「或」关系：影片关联的任一标签名与列表中的
某项精确匹配（忽略首尾空格和大小写）即判为合集。例如配置 `"tag_names": ["VR", "4時間以上作品"]` 时，
带有 `VR` 或 `4時間以上作品` 标签的影片都会被判定为合集。

插件任务名为 `sakuramedia_judge_collecttion_movie`，默认每天凌晨 4 点执行，也可以通过
宿主的任务中心手动触发。

在 APP 内手动标记的合集和单体不会被此插件覆盖。

## 多语言 / i18n

本插件声明 Host API 12，支持 `zh-CN` / `en`：

- 语言包放在 `i18n/zh-CN.json`、`i18n/en.json`，两个文件 key 集合必须一致；
  `translations.py` 只在导入时读取它们，生成静态 `*_i18n` 字典。
- 插件名：`manifest.json` 的 `display_name_i18n` +
  `PluginRegistration.display_name_i18n`。
- 任务说明：`JobDefinition.cli_help_i18n`。
- 设置项标题：Pydantic `Field` 的
  `json_schema_extra={"title_i18n": text_map("settings.<字段名>.title")}`。
- 运行时文本（任务进度）：
  `context.i18n.t("jobs.judge.progress", default=..., **params)`。
- 所有 `*_i18n` 字段都是可选的，缺失时宿主回退到插件原文；新增语言时在
  `i18n/` 增加同名 JSON，并补上 manifest / registration 的
  `display_name_i18n`。

## License

本项目采用 [PolyForm Noncommercial License 1.0.0](./LICENSE)，仅允许非商业用途。

Copyright (C) 2026 tinypinglite

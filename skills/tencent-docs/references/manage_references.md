# 文件管理（manage.*）工具地图

> **本 fork 删除了原版的逐工具 API 手册**：参数、返回值一律以会话内 `tools/list` 返回的实时 Schema 为准。本文只保留"动作 → 工具"的路由价值和跨工具约定。

## 文件夹操作

- 列出文件夹内容：`manage.folder_list`
- 查询文件夹元信息：`manage.query_folder_meta`

## 创建与搜索

- 创建文件 / 文件夹 / 链接：`manage.create_file`（支持 doc、sheet、智能文档、收集表、幻灯片、思维导图、流程图、智能表格、文件夹、链接；`space_id` 不为空时在知识库空间中创建节点，为空时在个人首页创建）
- 搜索文档：`manage.search_file`（关键词 → `file_id`）
- 查询文件信息（含 doc_type）：`manage.query_file_info`
- 最近浏览列表：`manage.recent_online_file`

## 重命名 / 移动 / 复制 / 删除

- 重命名：`manage.rename_file_title`
- 移动（个人网盘内）：`manage.move_file`
- 移动到知识库空间：`manage.move_file_to_space`
- 复制：`manage.copy_file`
- 删除：`manage.delete_file`

## 权限

- 查询权限：`manage.get_privilege`
- 设置权限：`manage.set_privilege`

## 导入 / 导出（配合本地脚本）

- 预导入（计算 MD5、取 COS 上传链接与 file_key）：`manage.pre_import`（由 `import_file.sh` 封装）
- 触发异步导入：`manage.async_import`
- 导入进度轮询：`manage.import_progress`
- 导出文件：`manage.export_file`，进度查询 `manage.export_progress`

## 跨工具约定

- `node_id` 即 `file_id`（空间节点与文档同 ID）
- 编辑前先通过 `manage.query_file_info` 或文档链接前缀确认 `doc_type`，再按 SKILL.md 场景路由表选择对应品类工具集
- 本地文件上云统一走 `import_file.sh` → `manage.async_import` → `manage.import_progress` 通路，保留原文件结构，不要用 `create_*` 工具重新生成内容

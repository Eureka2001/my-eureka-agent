# 智能表格（smartsheet）操作参考

> **本 fork 删除了原版的逐工具 API 手册**：各工具的参数级细节以会话内 `tools/list` 返回的实时 Schema 为准。本文保留概念模型、工具地图、枚举值、字段值格式、字段属性结构与典型工作流——这些是 MCP Schema 之外的领域知识，不会随工具参数微调而失效。

## 概念说明

| 概念 | 说明 |
|------|------|
| `file_id` | 智能表格文档的唯一标识符，每个文档有唯一的 file_id |
| `sheet_id` | 工作表 ID，一个智能表格文档可包含多个工作表 |
| `view_id` | 视图 ID，每个工作表可有多个视图（表格视图、看板视图等） |
| `field_id` | 字段 ID，对应表格的列 |
| `record_id` | 记录 ID，对应表格的行 |

**层级关系**：`file_id（文档）` → `sheet_id（工作表）` → `view_id（视图）` / `field_id（字段）` / `record_id（记录）`

## 工具地图

- 工作表：`smartsheet.list_tables` / `smartsheet.add_table` / `smartsheet.delete_table`
- 视图：`smartsheet.list_views` / `smartsheet.add_view` / `smartsheet.update_view` / `smartsheet.delete_view`
- 字段：`smartsheet.list_fields` / `smartsheet.add_fields` / `smartsheet.update_fields` / `smartsheet.delete_fields`
- 记录：`smartsheet.list_records` / `smartsheet.add_records` / `smartsheet.update_records` / `smartsheet.delete_records`
- 变更集：`smartsheet.commit_changeset` / `smartsheet.fetch` / `smartsheet.get_client_var`
- 仪表盘（按计划生成）：`smartsheet.create_dashboard_from_plan` / `smartsheet.add_dashboard_component_from_plan` / `smartsheet.update_dashboard_component_from_plan` / `smartsheet.get_dashboard` / `smartsheet.get_dashboard_component` / `smartsheet.delete_dashboard_component`
- 自动化（按计划生成）：`smartsheet.create_automation_from_plan` / `smartsheet.update_automation_from_plan` / `smartsheet.list_automations` / `smartsheet.delete_automation`
- 建表（按计划生成）：`smartsheet.create_table_from_plan`

---

## 枚举值参考

### 字段类型（field_type）

| 枚举值 | 类型名称 | 对应 property 字段 | 说明 |
|--------|---------|-------------------|------|
| `text` | 文本 | `property_text` | 普通文本，无需额外配置 |
| `number` | 数字 | `property_number` | 整数或浮点数 |
| `checkbox` | 复选框 | `property_checkbox` | 布尔值 true/false |
| `dateTime` | 日期 | `property_date_time` | 毫秒时间戳字符串 |
| `image` | 图片 | `property_image` | 图片 ID 数组 |
| `url` | 超链接 | `property_url` | URL 数组 |
| `select` | 多选 | `property_select` | 选项数组（可多选） |
| `createdUser` | 创建人 | `property_user` | 系统自动填充，无需配置 |
| `modifiedUser` | 最后编辑人 | `property_modified_user` | 系统自动填充，无需配置 |
| `createdTime` | 创建时间 | `property_created_time` | 系统自动填充，无需配置 |
| `modifiedTime` | 最后编辑时间 | `property_modified_time` | 系统自动填充，无需配置 |
| `progress` | 进度 | `property_progress` | 整数或浮点数（百分比） |
| `phoneNumber` | 电话 | `property_phone_number` | 字符串，无需额外配置 |
| `email` | 邮件 | `property_email` | 字符串，无需额外配置 |
| `singleSelect` | 单选 | `property_single_select` | 选项数组（只能单选） |
| `reference` | 关联 | - | 关联其他记录，值为 record_id 字符串数组 |
| `autoNumber` | 自动编号 | - | 系统自动生成编号，无需手动配置 |
| `currency` | 货币 | - | 浮点数，表示货币金额 |
| `percentage` | 百分比 | - | 浮点数，如 0.75 表示 75% |

### 视图类型（view_type）

| 枚举值 | 说明 |
|--------|------|
| `grid` | 表格视图 - 传统表格形式 |
| `kanban` | 看板视图 - 按列分组展示 |

### 选项颜色（style）

| 枚举值 | 颜色 |
|--------|------|
| `1` | 红色 |
| `2` | 橘黄色 |
| `3` | 蓝色 |
| `4` | 绿色 |
| `5` | 紫色 |
| `6` | 粉色 |
| `7` | 灰色 |
| `8` | 白色 |

### 超链接展示样式（UrlFieldProperty.type）

| 枚举值 | 说明 |
|--------|------|
| `0` | 未知 |
| `1` | 文字 |
| `2` | 图标文字 |

---

## 字段值格式参考

在 `add_records` 和 `update_records` 中，`field_values` 是一个 `FieldValueEntry` 数组，每个元素包含 `field`（字段标题）和一个 oneof 值字段。根据字段类型选择对应的值字段：

| 字段类型 | 使用的 oneof 值字段 | 示例 |
|---------|-------------------|------|
| 文本（text） | `text_value` | `{"field": "标题", "text_value": {"items": [{"text": "内容", "type": "text"}]}}` |
| 数字（number） | `number_value` | `{"field": "数量", "number_value": 42}` |
| 复选框（checkbox） | `bool_value` | `{"field": "已完成", "bool_value": true}` |
| 日期（dateTime） | `string_value` | `{"field": "日期", "string_value": "1720000000000"}` |
| 图片（image） | `image_value` | `{"field": "封面", "image_value": {"items": [{"image_id": "图片id"}]}}` |
| 超链接（url） | `url_value` | `{"field": "链接", "url_value": {"items": [{"text": "链接文字", "type": "url", "link": "https://..."}]}}` |
| 多选（select） | `option_value` | `{"field": "标签", "option_value": {"items": [{"text": "选项1"}, {"text": "选项2"}]}}` |
| 进度（progress） | `number_value` | `{"field": "进度", "number_value": 75}` |
| 电话（phoneNumber） | `string_value` | `{"field": "电话", "string_value": "13800138000"}` |
| 邮件（email） | `string_value` | `{"field": "邮箱", "string_value": "user@example.com"}` |
| 单选（singleSelect） | `option_value` | `{"field": "状态", "option_value": {"items": [{"text": "选项文字"}]}}` |
| 关联（reference） | `reference_value` | `{"field": "关联", "reference_value": {"items": ["record_id_1", "record_id_2"]}}` |
| 自动编号（autoNumber） | `auto_number_value` | `{"field": "编号", "auto_number_value": {"seq": "1", "text": "编号内容"}}` |
| 货币（currency） | `number_value` | `{"field": "金额", "number_value": 99.99}` |
| 百分比（percentage） | `number_value` | `{"field": "占比", "number_value": 0.75}` |

### TextValueList 结构

```json
{
  "items": [
    {"text": "文本内容", "type": "text"}
  ]
}
```

### UrlValueList 结构

```json
{
  "items": [
    {"text": "链接显示文字", "type": "url", "link": "https://example.com"}
  ]
}
```

### OptionValueList 结构

```json
{
  "items": [
    {"id": "选项ID（可选）", "text": "选项文字", "style": "3"}
  ]
}
```

### ImageIDValueList 结构

```json
{
  "items": [
    {"image_id": "图片ID"}
  ]
}
```

### StringValueList 结构（关联字段）

```json
{
  "items": ["record_id_1", "record_id_2"]
}
```

### AutoNumberValue 结构

```json
{
  "seq": "1",
  "text": "编号内容"
}
```

> ⚠️ **注意**：写入记录时，单选/多选字段的 `text` 必须与字段属性中已定义的选项文字完全匹配，否则可能写入失败。

---

## 字段属性（Property）详细说明

### NumberFieldProperty（数字字段属性）

```json
{
  "decimal_places": 2,
  "use_separate": true
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `decimal_places` | uint32 | 小数点位数（精度） |
| `use_separate` | bool | 是否使用千位符（如 1,000） |

### CheckboxFieldProperty（复选框字段属性）

```json
{
  "checked": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `checked` | bool | 新增记录时是否默认勾选 |

### DateTimeFieldProperty（日期时间字段属性）

```json
{
  "format": "yyyy-mm-dd",
  "auto_fill": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `format` | string | 日期格式，支持格式见下方 |
| `auto_fill` | bool | 新建记录时是否自动填充当前时间 |

**支持的日期格式**：

| 格式字符串 | 示例 |
|-----------|------|
| `yyyy"年"m"月"d"日"` | 2018 年 4 月 20 日 |
| `yyyy-mm-dd` | 2018-04-20 |
| `yyyy/m/d` | 2018/4/20 |
| `m"月"d"日"` | 4 月 20 日 |
| `[$-804]yyyy"年"m"月"d"日" dddd` | 2018 年 4 月 20 日 星期五 |
| `yyyy"年"m"月"d"日" hh:mm` | 2018 年 4 月 20 日 14:00 |
| `yyyy-mm-dd hh:mm` | 2018-04-20 14:00 |
| `m/d/yyyy` | 4/20/2018 |
| `d/m/yyyy` | 20/4/2018 |

### UrlFieldProperty（超链接字段属性）

```json
{
  "type": 1
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | uint32 | 展示样式：0-未知，1-文字，2-图标文字 |

### SelectFieldProperty（多选字段属性）

```json
{
  "options": [
    { "id": "opt_001", "text": "选项A", "style": 3 },
    { "id": "opt_002", "text": "选项B", "style": 4 }
  ],
  "is_multiple": true,
  "is_quick_add": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `options` | []Option | 选项列表 |
| `is_multiple` | bool | 是否多选（系统参数，用户无需设置） |
| `is_quick_add` | bool | 是否允许填写时新增选项（系统参数，用户无需设置） |

### SingleSelectFieldProperty（单选字段属性）

结构与 `SelectFieldProperty` 相同，但只允许单选。

### ProgressFieldProperty（进度字段属性）

```json
{
  "decimal_places": 0
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `decimal_places` | uint32 | 小数位数 |

---

## 典型工作流示例

### 工作流一：从零创建表

```
步骤 1：获取文档的工作表列表
  → smartsheet.list_tables（获取 sheet_id）

步骤 2：为工作表添加字段
  → smartsheet.add_fields（添加：任务名称、优先级、负责人、截止日期、状态、进度）

步骤 3：批量添加任务记录
  → smartsheet.add_records（写入多条任务数据）

步骤 4：删除默认空行和默认列
  → smartsheet.list_records（获取建表时自动生成的空行 record_id 列表）
  → smartsheet.delete_records（传入空行 record_ids，批量删除默认空行）
  → smartsheet.list_fields（获取建表时自动生成的默认列 field_id 列表）
  → smartsheet.delete_fields（传入默认列 field_ids，批量删除默认列）

步骤 5：（可选）创建看板视图
→ smartsheet.add_view（view_type="kanban"，按状态分组）
```

### 工作流二：查询并更新任务状态

```
步骤 1：列出工作表
  → smartsheet.list_tables（获取 sheet_id）

步骤 2：查询记录
  → smartsheet.list_records（获取 record_id 和当前字段值）

步骤 3：更新指定记录
  → smartsheet.update_records（传入 record_id 和新的字段值）
```

### 工作流三：读取数据并分析

```
步骤 1：列出工作表
  → smartsheet.list_tables

步骤 2：了解字段结构
  → smartsheet.list_fields（了解有哪些列及其类型）

步骤 3：分页读取所有记录
  → smartsheet.list_records（offset=0, limit=100）
  → 若 has_more=true，继续请求下一页（offset=100）

步骤 4：处理数据
  → 根据 field_values 中的数据进行统计分析
```

### 工作流四：清理过期数据

```
步骤 1：列出工作表
  → smartsheet.list_tables

步骤 2：查询需要删除的记录
  → smartsheet.list_records（获取目标 record_id 列表）

步骤 3：批量删除记录
  → smartsheet.delete_records（传入 record_ids 数组）
```

---

## 注意事项

- **前置条件**：所有 smartsheet.* 工具都需要 `file_id` 和 `sheet_id`，操作前先调用 `smartsheet.list_tables` 获取 sheet_id
- **图片字段写入**：向图片类型字段（field_type=image）写入数据时，需先调用 `upload_image` 工具上传图片获取 `image_id`，再以 `[{"image_id": "xxx"}]` 格式填入字段值
- **字段类型不可变**：`update_fields` 时 `field_type` 不能修改，但必须传入原值；支持的字段类型详见字段类型枚举表
- **记录字段值格式**：不同字段类型的值格式不同，详见上方"字段值格式参考"章节

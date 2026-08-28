# 自动化工具

## 推荐组合

现代 Python 项目建议至少使用以下工具。

- Ruff：Lint、导入排序和格式化
- Pyright、mypy 或 ty：静态类型检查
- pytest：自动化测试
- pre-commit：提交前执行检查，可选

Ruff 可以覆盖大量传统工具的常见功能，包括 Flake8、isort、pyupgrade 和部分 pydocstyle 规则。

## Ruff 基础配置

下面是一份适合新项目的起始配置。启用规则应根据项目需要逐步调整，不要一次打开全部规则后大量忽略。

```toml
[tool.ruff]
line-length = 88
indent-width = 4
target-version = "py310"

[tool.ruff.lint]
select = [
    "E4",
    "E7",
    "E9",
    "F",
    "B",
    "I",
    "UP",
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

规则组含义如下。

| 规则组 | 作用 |
|---|---|
| `E4`、`E7`、`E9` | 常见格式、语句和严重语法问题 |
| `F` | Pyflakes：未定义名称、未使用导入等 |
| `B` | flake8-bugbear：常见缺陷和设计问题 |
| `I` | 导入排序 |
| `UP` | 建议使用现代 Python 语法 |

## 常用命令

本地自动修复并格式化：

```bash
ruff check . --fix
ruff format .
```

持续集成环境只检查、不修改：

```bash
ruff check .
ruff format . --check
```

类型检查和测试命令由项目选择的工具决定，例如：

```bash
pyright
pytest
```

## 工具与人工审查的边界

工具适合检查以下内容。

- 空格、换行和引号
- 导入顺序
- 未使用名称
- 常见错误模式
- 类型不一致

人工审查仍需关注以下内容。

- 名称是否准确
- 函数职责是否单一
- 数据流和控制流是否清晰
- 接口抽象是否合理
- 异常是否包含合适上下文
- 注释是否解释了真正需要解释的原因
- 测试是否覆盖关键行为

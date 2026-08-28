---
name: python-code-style-guide
description: This skill should be used when reviewing, refactoring, styling, or generating Python code according to this repository's general style guide and personal engineering conventions. It applies to Python code reviews, maintainability checks, style fixes, CLI tool development, and requests to follow the user's Python conventions.
agent_created: true
---

# Python 代码审查与风格化

按照本目录中的规范，对 Python 代码执行审查、风格化、重构或生成。将本文件作为执行入口，将 [README.md](README.md) 作为规范总索引；不要在本文件中重复维护具体代码规则。

## 读取顺序

1. 读取 [README.md](README.md)，确认规范定位、适用范围和章节结构。
2. 查找并读取目标项目已有的 `AGENTS.md`、`CONTRIBUTING.md`、`README.md`、`pyproject.toml` 及相关工具配置。
3. 读取 [个人 Python 工程偏好](personal-python-conventions.md)。
4. 判断任务属于只读审查、风格化与修复，还是代码生成。
5. 根据任务涉及的主题，按“规范读取路由”选择性读取 `docs/` 中的章节；不要无条件加载全部文件。

## 规则优先级

发生冲突时，按照以下顺序处理：

1. 用户在当前任务中的明确要求
2. 目标项目已有的明确约定
3. [个人 Python 工程偏好](personal-python-conventions.md)
4. `docs/` 中的通用 Python 代码规范

优先保持目标项目内部一致。因兼容性、框架限制或外部接口要求不能应用某项规则时，保留合理例外并说明原因，不进行机械修改。

## 工作模式

### 只读审查

当用户要求“检查”“审查”“分析是否符合规范”或表达相同意图，但没有明确要求修改时：

1. 读取待审查代码及其直接相关上下文。
2. 读取项目约定、个人偏好和相关规范章节。
3. 识别明确违规、可维护性问题和合理例外。
4. 按“审查输出”报告结果。
5. 不修改任何文件，不运行会改写文件的格式化或修复命令。

### 风格化与修复

仅当用户明确要求修改、修复、重构或风格化代码时：

1. 先完成审查并确定修改范围。
2. 区分纯风格调整与可能改变行为的修改。
3. 采用最小必要改动，不顺带重写无关代码。
4. 不擅自改变程序行为、公共 API、CLI 兼容性、配置格式或持久化数据格式。
5. 遵循目标项目现有格式化、Lint、类型检查和测试配置。
6. 执行适用的验证，并准确报告已运行和未运行的检查。

### 代码生成

当用户要求新增 Python 代码或工具时：

1. 先了解目标项目结构、现有接口和工具链。
2. 读取个人偏好及与任务相关的通用规范章节。
3. 生成与项目现有代码协调且符合规范的新代码。
4. 执行适用的格式化、Lint、类型检查和测试。
5. 说明新增文件、关键设计选择和验证结果。

## 规范读取路由

| 任务或问题 | 读取文件 |
| --- | --- |
| 所有适用任务 | [README.md](README.md) |
| 所有代码审查、修改和生成任务 | [personal-python-conventions.md](personal-python-conventions.md) |
| 全面代码审查 | [docs/review-checklist.md](docs/review-checklist.md)、[docs/principles.md](docs/principles.md) |
| 命名、变量和常量 | [docs/naming.md](docs/naming.md)、[docs/variables-and-constants.md](docs/variables-and-constants.md) |
| 文件、模块和项目组织 | [docs/files-and-modules.md](docs/files-and-modules.md)、[docs/project-structure.md](docs/project-structure.md) |
| 排版、空格、换行和导入 | [docs/layout.md](docs/layout.md)、[docs/whitespace.md](docs/whitespace.md)、[docs/imports.md](docs/imports.md) |
| 函数、类和公共接口 | [docs/functions.md](docs/functions.md)、[docs/classes-and-interfaces.md](docs/classes-and-interfaces.md) |
| 类型设计 | [docs/type-annotations.md](docs/type-annotations.md) |
| 条件、循环和推导式 | [docs/control-flow.md](docs/control-flow.md) |
| 异常、文件和资源管理 | [docs/exceptions-and-resources.md](docs/exceptions-and-resources.md) |
| 注释和文档字符串 | [docs/comments-and-docstrings.md](docs/comments-and-docstrings.md) |
| 日志 | [docs/logging.md](docs/logging.md) |
| 测试 | [docs/testing.md](docs/testing.md) |
| 格式化、Lint 和类型检查工具 | [docs/tooling.md](docs/tooling.md) |
| 查询规范依据 | [docs/references.md](docs/references.md) |

当一个问题同时涉及多个主题时，只加载直接相关的章节。全面审查先使用审查清单定位问题，再读取相应章节确认依据和边界。

## 审查输出

先给出总体结论，再按重要程度列出发现。每个发现至少包含：

- 规则来源：当前要求、项目约定、个人偏好或通用规范
- 代码位置：文件路径和行号
- 问题说明：解释为什么需要处理
- 修改建议：给出可执行且尽量局部的方案
- 处理判断：必须修复、建议修复、确认后修改或合理例外

优先报告影响可维护性、正确性和接口一致性的问题。不要为了凑数量报告无实际价值的细枝末节。没有发现问题时直接说明，并列出已检查的范围。

## 执行边界

- 排除虚拟环境、构建产物、缓存、第三方依赖和自动生成代码，除非用户明确要求检查。
- 不根据文件名猜测实现；先读取实际代码和项目配置。
- 不把格式偏好包装成正确性缺陷。
- 不因个人偏好破坏已有兼容性。
- 不声称未实际执行的检查、测试或命令已经通过。
- 发现规则之间存在歧义时，引用相关文件并说明判断依据。

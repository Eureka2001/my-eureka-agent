# Python 代码风格指南

本指南规定 Python 项目中的命名、排版、接口、类型注解、异常处理、注释、测试和工具配置。

它主要参考 PEP 8、PEP 257、Python Typing Best Practices、Google Python Style Guide、Black 与 Ruff，并针对现代 Python 项目作了取舍。

本指南默认面向 Python 3.10 及以上版本。项目如果需要兼容更早版本，应在项目规范中明确说明。

## 个人补充约定

[个人 Python 工程偏好](personal-python-conventions.md)记录了在通用规范之上的个人默认选择，包括日志、文件系统路径、Magic Number、配置对象和命令行接口。项目已有明确约定时，优先遵守项目约定。

## 作为 Skill 使用

本目录同时是一份可独立发布的规范文档和一个 Skill 源码包。人类读者从本文档进入，Agent 从 [SKILL.md](SKILL.md) 进入。

`SKILL.md` 只负责识别任务、选择工作模式和按需加载规范，不重复维护具体代码要求。执行代码审查、风格化或生成任务时，Agent 会先读取本文档和个人补充约定，再根据任务主题选择性读取 `docs/` 中的相关章节。

## 目录

1. [基本原则](docs/principles.md)
2. [命名](docs/naming.md)
3. [文件与模块](docs/files-and-modules.md)
4. [代码布局](docs/layout.md)
5. [空格与换行](docs/whitespace.md)
6. [导入](docs/imports.md)
7. [变量与常量](docs/variables-and-constants.md)
8. [函数](docs/functions.md)
9. [类与接口](docs/classes-and-interfaces.md)
10. [类型注解](docs/type-annotations.md)
11. [条件、循环与推导式](docs/control-flow.md)
12. [异常与资源管理](docs/exceptions-and-resources.md)
13. [注释与文档字符串](docs/comments-and-docstrings.md)
14. [日志](docs/logging.md)
15. [测试代码](docs/testing.md)
16. [项目结构](docs/project-structure.md)
17. [自动化工具](docs/tooling.md)
18. [代码审查清单](docs/review-checklist.md)
19. [参考资料](docs/references.md)

## 使用建议

- 新项目可以先阅读“基本原则”“命名”“函数”和“自动化工具”。
- 代码审查时可以直接使用“代码审查清单”。
- 项目已有明确规范时，优先保持项目内一致，再逐步迁移。
- 不要在功能修改中混入大规模无关格式变更。

## 文件结构

```text
python-code-style-guide/
├── README.md
├── SKILL.md
├── personal-python-conventions.md
└── docs/
    ├── principles.md
    ├── naming.md
    ├── files-and-modules.md
    ├── layout.md
    ├── whitespace.md
    ├── imports.md
    ├── variables-and-constants.md
    ├── functions.md
    ├── classes-and-interfaces.md
    ├── type-annotations.md
    ├── control-flow.md
    ├── exceptions-and-resources.md
    ├── comments-and-docstrings.md
    ├── logging.md
    ├── testing.md
    ├── project-structure.md
    ├── tooling.md
    ├── review-checklist.md
    └── references.md
```

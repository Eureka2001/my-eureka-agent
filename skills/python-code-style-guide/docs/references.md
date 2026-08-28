# 参考资料

## 主要依据

1. [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
2. [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
3. [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
4. [Google Python Style Guide 中文翻译](https://zh-google-styleguide.readthedocs.io/en/latest/google-python-styleguide/contents.html)
5. [Python Typing Best Practices](https://typing.python.org/en/latest/reference/best_practices.html)
6. [The Black Code Style](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html)
7. [Ruff Documentation](https://docs.astral.sh/ruff/)
8. [Ruff Configuration](https://docs.astral.sh/ruff/configuration/)

## 采用说明

本指南不是上述任一文档的逐字翻译，而是面向现代 Python 项目的中文汇总。

主要取舍如下。

- 命名、导入、异常、公共接口等基础原则以 PEP 8 为主。
- 文档字符串的基本结构以 PEP 257 为主。
- 工程设计、注释、异常边界和工具使用参考 Google Python Style Guide。
- 类型注解参考 Python 官方 Typing Best Practices，并默认采用 Python 3.10 及以上语法。
- 行长采用 Black 和 Ruff 默认的 88 字符，而不是 PEP 8 的 79 字符。
- 自动化工具推荐 Ruff，但 Ruff 不能替代命名、职责和接口设计方面的人工审查。

如果项目现有规则与本指南冲突，应先保持项目内一致，再通过单独的格式化提交完成迁移。不要在功能修改中混入大规模无关格式变更。

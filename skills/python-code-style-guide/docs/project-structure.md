# 项目结构

## 推荐结构

中小型应用可以采用下面的结构。

```text
project/
├── pyproject.toml
├── README.md
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── config.py
│       ├── models.py
│       └── services/
└── tests/
    ├── conftest.py
    └── test_config.py
```

是否采用 `src` 布局取决于项目规模和发布方式。无论选择哪种布局，都应保证导入路径在本地、测试和生产环境中保持一致。

## 配置集中化

格式化、Lint、测试和类型检查配置优先集中放入 `pyproject.toml`，避免同一规则分散在多个文件中。

## 依赖方向

底层模块不应反向依赖高层业务流程。公共数据类型和接口应放在职责明确的模块中，不要为了消除循环导入把所有内容堆入 `common.py`。

# 代码布局

## 缩进

每一级缩进使用 4 个空格。不要使用 Tab，也不要混用 Tab 和空格。

```python
def load_user(user_id: int) -> User:
    if user_id <= 0:
        raise ValueError("user_id must be positive")
    return repository.get(user_id)
```

## 行长

本指南建议每行最多 88 个字符，与 Black 和 Ruff 的默认格式兼容。

如果项目严格采用 PEP 8，可以将代码行限制为 79 个字符，将注释和文档字符串限制为 72 个字符。

不要为了满足行长限制而使用难懂的缩写。应优先调整表达式结构。

## 空行

（1）顶层类和函数之间空两行。

（2）类内方法之间空一行。

（3）函数内部可以使用单个空行划分逻辑阶段，但不要把每条语句都隔开。

```python
def load_and_validate(path: Path) -> Config:
    raw_config = path.read_text(encoding="utf-8")
    config = parse_config(raw_config)

    validate_config(config)
    return config
```

## 一行一条语句

不要使用分号把多条语句放在同一行。

```python
# 不推荐
user = load_user(); validate_user(user)

# 推荐
user = load_user()
validate_user(user)
```

不要把带有复杂逻辑的 `if`、`for` 或 `while` 压缩成一行。

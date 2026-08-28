# 注释与文档字符串

## 注释

（1）注释应解释“为什么”，而不是逐句重复代码。

```python
# 不推荐：将重试次数加一
retry_count += 1

# 推荐：首次请求不计入退避次数，因此失败后再递增
retry_count += 1
```

（2）注释必须与代码同步。错误或过期的注释比没有注释更危险。

（3）行内注释应少用，与代码之间至少保留两个空格。

```python
port = 8080  # 与本地开发代理保持一致
```

（4）待办事项应说明责任、原因或跟踪信息，不能只写模糊的 `TODO`。

```python
# 不推荐
# TODO: fix this

# 推荐
# TODO(issue-184): 删除旧协议兼容分支。
```

## 文档字符串

所有公共模块、类、函数和方法都应有文档字符串。逻辑复杂的重要内部函数也应有文档字符串。

文档字符串使用三重双引号。

```python
def normalize_name(name: str) -> str:
    """Normalize a user-provided display name."""
```

单行文档字符串应满足以下要求。

- 开始和结束引号位于同一行。
- 使用祈使语气描述行为，例如 `Return`、`Load`、`Validate`。
- 不重复函数签名。
- 以句号结束。

多行文档字符串由摘要行、空行和详细说明组成。

```python
def load_config(path: Path, required: bool = True) -> Config | None:
    """Load application configuration from a file.

    Args:
        path: Configuration file path.
        required: Whether a missing file is considered an error.

    Returns:
        Parsed configuration. Returns None when the file is optional
        and does not exist.

    Raises:
        ConfigError: The file exists but cannot be parsed.
    """
```

有类型注解时，文档字符串不重复显而易见的类型，而应说明以下内容。

- 参数语义和单位
- 合法范围和限制
- 返回值含义
- 可观察副作用
- 调用者需要处理的重要异常

## 模块文档字符串

模块文档字符串用于说明模块职责和重要用法，不要只重复文件名。

```python
"""Load, validate, and merge application configuration files."""
```

测试模块如果没有特殊运行方式、外部依赖或固定数据更新方法，可以不写没有信息量的模块文档字符串。

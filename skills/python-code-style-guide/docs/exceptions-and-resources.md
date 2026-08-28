# 异常与资源管理

## 异常类型

（1）参数值不合法通常抛出 `ValueError`。

（2）参数类型不合法通常抛出 `TypeError`。

（3）查找不到键时，根据接口语义选择 `KeyError`、返回 `None` 或自定义异常。

（4）自定义错误应继承 `Exception` 或更具体的异常类，不要直接继承 `BaseException`。

```python
class ConfigError(ValueError):
    """Represent an invalid application configuration."""
```

## 捕获异常

捕获最具体的异常，不要使用裸 `except`。

```python
# 不推荐
try:
    config = load_config(path)
except:
    config = default_config()

# 推荐
try:
    config = load_config(path)
except FileNotFoundError:
    config = default_config()
```

只有在程序边界处记录和隔离未知错误时，才考虑捕获 `Exception`。

## `try` 范围

`try` 块只包含可能抛出目标异常的最少代码。

```python
# 不推荐
try:
    raw_text = path.read_text(encoding="utf-8")
    config = parse_config(raw_text)
    start_service(config)
except ValueError:
    ...

# 推荐
raw_text = path.read_text(encoding="utf-8")
try:
    config = parse_config(raw_text)
except ValueError as error:
    raise ConfigError(f"Invalid configuration: {path}") from error

start_service(config)
```

## 异常链

转换异常时使用 `raise ... from ...` 保留原因。

```python
try:
    config = parse_config(raw_text)
except ValueError as error:
    raise ConfigError(f"Invalid configuration: {path}") from error
```

异常信息应说明失败对象和必要上下文，但不得包含密码、令牌等敏感信息。

## `assert`

`assert` 用于验证程序内部不变量，不用于校验公共 API 参数或处理业务错误。

```python
# 不推荐
assert timeout_seconds > 0, "timeout must be positive"

# 推荐
if timeout_seconds <= 0:
    raise ValueError("timeout_seconds must be positive")
```

## 资源管理

文件、锁、连接和临时资源优先使用上下文管理器。

```python
with path.open("r", encoding="utf-8") as file:
    content = file.read()
```

不要依赖垃圾回收器决定资源释放时间。

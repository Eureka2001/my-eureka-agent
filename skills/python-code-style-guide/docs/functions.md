# 函数

## 单一职责

一个函数应完成一个明确任务。

如果函数名称需要使用多个不相关的动词，或者函数同时负责读取、转换、保存和通知，通常应该拆分。

```python
# 不推荐
def load_transform_save_and_notify(path: Path) -> None:
    ...

# 推荐
def load_records(path: Path) -> list[Record]:
    ...


def transform_records(records: Iterable[Record]) -> list[Record]:
    ...


def save_records(records: Iterable[Record]) -> None:
    ...
```

流程编排函数可以调用这些单一职责函数，以清晰表达执行顺序。

## 参数

（1）参数名应表达语义和单位。

```python
# 不推荐
def wait(timeout: float):
    ...

# 推荐
def wait(timeout_seconds: float) -> None:
    ...
```

（2）参数过多通常意味着函数职责过重，或多个参数应组成一个数据对象。

```python
@dataclass(frozen=True)
class RequestOptions:
    timeout_seconds: float
    max_retries: int
    verify_certificate: bool
```

（3）布尔参数会隐藏调用含义。必要时使用仅限关键字参数，或拆分为两个明确接口。

```python
# 不清楚 True 的含义
save_report(report, True)

# 更清楚
save_report(report, overwrite=True)
```

（4）不要使用可变对象作为默认参数。

```python
# 不推荐
def append_user(user: User, users: list[User] = []) -> list[User]:
    users.append(user)
    return users

# 推荐
def append_user(
    user: User,
    users: list[User] | None = None,
) -> list[User]:
    if users is None:
        users = []
    users.append(user)
    return users
```

## 返回值

（1）同一函数的返回形式应保持一致。

```python
# 不推荐
def find_user(user_id: int):
    if user_id in users:
        return users[user_id]
    return

# 推荐
def find_user(user_id: int) -> User | None:
    if user_id in users:
        return users[user_id]
    return None
```

（2）返回多个不同含义的值时，优先使用数据类、命名元组或明确的结果对象。

```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: tuple[str, ...]
```

（3）不要用特殊数字或空字符串隐式表示失败。需要区分多种状态时，应使用明确类型或异常。

## 副作用

函数名和文档应反映明显副作用，例如写文件、修改状态或发送请求。

查询函数原则上不应悄悄修改对象状态。

```python
# 不推荐：名称像查询，实际会更新缓存
def get_user(user_id: int) -> User:
    ...

# 更清楚
def get_or_cache_user(user_id: int) -> User:
    ...
```

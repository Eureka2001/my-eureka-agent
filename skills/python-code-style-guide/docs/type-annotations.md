# 类型注解

## 基本要求

（1）公共函数、公共方法和重要内部接口应标注参数类型和返回类型。

```python
def load_users(path: Path) -> list[User]:
    ...
```

（2）没有返回值的函数明确标注 `-> None`。

```python
def clear_cache() -> None:
    ...
```

（3）类型注解用于静态检查，不代替运行时的数据校验。

## 现代写法

Python 3.10 及以上版本优先使用内置泛型和 `|` 联合类型。

```python
# 推荐
def find_user(user_id: int) -> User | None:
    ...


def group_users(users: list[User]) -> dict[str, list[User]]:
    ...
```

需要兼容旧版本时，可以使用 `typing.Optional`、`typing.List` 等旧写法，但项目内必须统一。

## 参数和返回类型

参数优先接受满足需求的抽象接口，返回值优先声明实际返回的具体类型。

```python
from collections.abc import Iterable, Mapping


def parse_names(names: Iterable[str]) -> list[str]:
    ...


def copy_config(config: Mapping[str, str]) -> dict[str, str]:
    ...
```

这样可以让调用者传入列表、元组或其他可迭代对象，同时明确函数实际返回列表或字典。

## `Any` 与 `object`

如果函数可以接收任意对象，但不会任意调用其属性，应使用 `object`，而不是 `Any`。

```python
def format_value(value: object) -> str:
    return str(value)
```

`Any` 会跳过大量类型检查，只应在类型系统无法合理表达对象，或与无类型第三方接口交互时使用。

## 类型别名

复杂类型可以定义类型别名，但别名必须能提高可读性。

Python 3.12 及以上版本可以使用 `type` 语句。

```python
type UserById = dict[int, User]
type Coordinate = tuple[float, float]
```

需要兼容 Python 3.10 或 3.11 时，可以使用 `TypeAlias`。

```python
from typing import TypeAlias

Coordinate: TypeAlias = tuple[float, float]
```

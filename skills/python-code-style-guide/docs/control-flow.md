# 条件、循环与推导式

## `None` 判断

与 `None` 比较时使用 `is` 或 `is not`。

```python
# 不推荐
if value == None:
    ...

# 推荐
if value is None:
    ...
```

## 布尔判断

不要与 `True` 或 `False` 显式比较。

```python
# 不推荐
if is_valid == True:
    ...

# 推荐
if is_valid:
    ...
```

空字符串、空列表和空字典可以直接进行真值判断。

```python
if not users:
    return []
```

如果 `None` 与空容器具有不同含义，应明确判断 `None`。

## 类型判断

使用 `isinstance()`，不要直接比较 `type()`。

```python
# 不推荐
if type(value) is str:
    ...

# 推荐
if isinstance(value, str):
    ...
```

## 循环

优先直接迭代对象。

```python
# 不推荐
for index in range(len(users)):
    user = users[index]

# 推荐
for user in users:
    ...
```

同时需要索引时使用 `enumerate()`。

```python
for index, user in enumerate(users):
    ...
```

同时遍历多个序列时使用 `zip()`。

```python
for user, score in zip(users, scores, strict=True):
    ...
```

`strict=True` 适用于 Python 3.10 及以上版本，并且只应在两个序列长度必须一致时使用。

## 推导式

推导式只用于简单、直观的映射和过滤。

```python
active_user_ids = [
    user.id
    for user in users
    if user.is_active
]
```

包含多层循环、多个复杂条件或副作用时，使用普通循环。

```python
# 不推荐
result = [
    transform(x, y)
    for x in groups
    for y in x.items
    if is_valid(x, y) and not is_duplicate(y)
]

# 推荐
result = []
for group in groups:
    for item in group.items:
        if not is_valid(group, item):
            continue
        if is_duplicate(item):
            continue
        result.append(transform(group, item))
```

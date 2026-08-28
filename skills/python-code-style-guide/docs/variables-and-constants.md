# 变量与常量

## 变量作用域

（1）变量应定义在尽可能小的作用域内。

（2）不要为了避免传参而使用可变全局变量。

（3）模块级常量使用全大写下划线。

```python
DEFAULT_TIMEOUT_SECONDS = 30
MAX_RETRY_COUNT = 3
```

（4）模块内部使用的常量可以增加单前导下划线。

```python
_INTERNAL_CACHE_SIZE = 128
```

## 赋值

不要让一个变量在同一作用域中表示不同概念。

```python
# 不推荐
result = load_users()
result = len(result)

# 推荐
users = load_users()
user_count = len(users)
```

复杂表达式应拆分为具有业务含义的中间变量。

```python
# 不推荐
if request.user and request.user.role in allowed_roles and not request.user.disabled:
    ...

# 推荐
user = request.user
has_allowed_role = user is not None and user.role in allowed_roles
is_available = user is not None and not user.disabled

if has_allowed_role and is_available:
    ...
```

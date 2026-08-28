# 命名

## 通用原则

（1）名称应说明对象的用途，不要只说明对象的类型。

```python
# 不推荐
user_list = load_users()
data_dict = load_config()
str_value = request.text

# 推荐
users = load_users()
config = load_config()
request_text = request.text
```

（2）名称应使用完整、常见的单词。只有行业内公认的缩写才可以直接使用。

```python
# 不推荐
usr = get_user()
msg_cnt = count_messages()

# 推荐
user = get_user()
message_count = count_messages()
```

`id`、`url`、`http`、`api`、`db` 等广泛使用的缩写可以保留。

（3）名称不应包含无实际含义的序号或状态词。

```python
# 不推荐
data1 = load_source()
data2 = transform(data1)
result_new = validate(data2)

# 推荐
source_records = load_source()
normalized_records = transform(source_records)
validation_result = validate(normalized_records)
```

（4）避免使用小写字母 `l`、大写字母 `I` 和大写字母 `O` 作为单字符名称。它们容易与数字 `1` 和 `0` 混淆。

## 命名形式

| 对象 | 命名形式 | 示例 |
|---|---|---|
| 包 | 简短的全小写单词 | `training`、`dataset` |
| 模块 | 小写下划线 | `data_loader.py` |
| 函数 | 小写下划线 | `load_dataset()` |
| 方法 | 小写下划线 | `calculate_score()` |
| 变量 | 小写下划线 | `batch_size` |
| 类 | 大驼峰 | `DataLoader` |
| 异常类 | 大驼峰，通常以 `Error` 结尾 | `ConfigError` |
| 常量 | 全大写下划线 | `MAX_RETRY_COUNT` |
| 内部名称 | 单前导下划线 | `_parse_config()` |
| 类型变量 | 简短大写或描述性大驼峰 | `T`、`KeyT` |

## 变量名

（1）普通变量使用小写字母，多个单词之间使用下划线。

```python
user_name = "Alice"
max_retry_count = 3
```

（2）布尔变量应体现判断含义，通常使用 `is`、`has`、`can`、`should` 等前缀。

```python
is_valid = True
has_permission = False
can_retry = retry_count < max_retry_count
should_refresh_cache = cache_age > max_cache_age
```

不要使用无法看出真假含义的名称。

```python
# 不推荐
flag = True
status = False
```

（3）集合名称通常使用复数形式。

```python
users = load_users()
image_paths = find_images()
user_by_id = {user.id: user for user in users}
```

（4）循环变量可以简短，但嵌套循环或业务含义明显时应使用描述性名称。

```python
# 可以接受
for index in range(10):
    ...

# 推荐
for user in users:
    ...

# 不推荐
for x in users:
    ...
```

## 函数名

函数名通常使用动词或动宾结构，说明函数执行的动作。

```python
load_config()
calculate_score()
validate_request()
convert_image_to_rgb()
```

返回布尔值的函数应体现判断语义。

```python
is_empty()
has_access()
can_publish()
should_retry()
```

不要使用含义过于宽泛的动词。

```python
# 不推荐
def process(data):
    ...

# 推荐
def normalize_user_records(records):
    ...
```

如果 `process`、`handle` 或 `execute` 是领域内明确的接口名称，可以保留，但应通过类名或模块名补足上下文。

## 类名

类名使用大驼峰形式，通常使用名词或名词短语。

```python
class UserRepository:
    ...


class CoordinateValidator:
    ...
```

缩写词在类名中可以全部大写，但项目内必须统一。

```python
class HTTPClient:
    ...


class JSONEncoder:
    ...
```

## 特殊下划线

（1）单前导下划线表示非公开实现。

```python
def _parse_internal_state(raw_state: str) -> dict[str, str]:
    ...
```

（2）名称与 Python 关键字冲突时，使用尾随下划线。

```python
class_ = "premium"
from_ = "cache"
```

不要故意拼错单词来避开关键字。

```python
# 不推荐
klass = "premium"
```

（3）双前导下划线会触发名称改写。只有确实需要避免子类名称冲突时才使用。

（4）双前导和双结尾下划线名称由 Python 保留。不要自行创造新的特殊名称。

```python
# 不推荐
def __serialize__():
    ...
```

# 空格与换行

## 运算符

赋值、比较和布尔运算符两侧通常各保留一个空格。

```python
total = subtotal + tax
is_ready = enabled and count > 0
retry_count += 1
```

不要用多个空格进行人为的纵向对齐。

```python
# 不推荐
name       = "Alice"
retry_count = 3

# 推荐
name = "Alice"
retry_count = 3
```

## 括号

函数调用、索引和切片的括号前不加空格。

```python
result = calculate_total(items)
first_user = users[0]
active_users = users[start:end]
```

括号内部不添加无意义的空格。

```python
# 不推荐
result = calculate_total( items )

# 推荐
result = calculate_total(items)
```

## 默认参数

没有类型注解时，默认参数的等号两侧不加空格。

```python
def connect(timeout=3.0):
    ...
```

有类型注解时，等号两侧加空格。

```python
def connect(timeout: float = 3.0) -> None:
    ...
```

## 多行结构

多行参数、列表、元组、集合和字典建议每行只放一项，并保留尾逗号。

```python
result = build_request(
    user_id=user_id,
    request_id=request_id,
    timeout=timeout,
)

SUPPORTED_FORMATS = [
    "jpg",
    "png",
    "webp",
]
```

尾逗号可以减少新增或删除元素时产生的无关 diff。

## 续行

使用圆括号、方括号或花括号进行隐式续行，不使用反斜杠。

```python
# 不推荐
is_valid = has_name and has_email \
    and has_permission

# 推荐
is_valid = (
    has_name
    and has_email
    and has_permission
)
```

较长的二元表达式建议在运算符之前换行。

```python
total_price = (
    product_price
    + shipping_fee
    - discount_amount
)
```

# 类与接口

## 类的职责

类应表示一个清晰概念，并维护与该概念相关的不变量。

只包含一组无状态工具方法的类通常没有必要，可以改为模块级函数。

## 属性

（1）简单公开数据可以直接使用属性，不需要机械编写 getter 和 setter。

```python
@dataclass
class User:
    name: str
    email: str
```

（2）需要验证、计算或保持兼容时，可以使用 `property`。

```python
class Rectangle:
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    @property
    def area(self) -> float:
        return self.width * self.height
```

不要用属性隐藏昂贵的网络请求或大量计算。调用者通常认为属性访问成本很低。

## 方法参数

实例方法的第一个参数使用 `self`，类方法的第一个参数使用 `cls`。

```python
class User:
    def display_name(self) -> str:
        ...

    @classmethod
    def from_json(cls, raw_text: str) -> "User":
        ...
```

## 继承

（1）优先组合，谨慎使用继承。

（2）公共方法、子类扩展点和内部方法应明确区分。

（3）重写父类方法时，应保持父类契约。若改变参数、返回值、副作用或异常行为，必须明确记录。

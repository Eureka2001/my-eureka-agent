# 测试代码

## 测试命名

测试文件使用 `test_*.py`，测试函数名称应说明条件和预期结果。

```python
def test_load_config_returns_default_when_optional_file_is_missing():
    ...
```

不要只使用无语义序号。

```python
# 不推荐
def test_case_1():
    ...
```

## 测试结构

测试应清楚区分准备、执行和断言三个阶段。简单测试不必机械添加注释，但结构必须明显。

```python
def test_calculate_total_applies_discount():
    items = [Item(price=100), Item(price=50)]

    total = calculate_total(items, discount=20)

    assert total == 130
```

## 测试原则

（1）一个测试主要验证一个行为。

（2）测试外部可观察行为，不要过度依赖内部实现。

（3）测试应相互独立，不依赖执行顺序。

（4）固定时间、随机数、网络和文件系统等不稳定依赖。

（5）异常测试应同时验证异常类型和关键错误信息。

```python
def test_load_config_rejects_invalid_json(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid configuration"):
        load_config(path)
```

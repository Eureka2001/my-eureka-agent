# 文件与模块

## 文件名

Python 文件名使用小写字母和下划线，不使用空格或连字符。

```text
不推荐：DataLoader.py
不推荐：data-loader.py
推荐：data_loader.py
```

可执行入口、测试文件和配置文件应遵循项目统一约定。

```text
main.py
test_data_loader.py
conftest.py
```

## 模块职责

（1）一个模块应围绕一个明确职责组织。

（2）当模块名称只能使用 `utils.py`、`helpers.py` 或 `common.py` 描述时，通常说明职责划分还不清楚。

```text
不推荐：utils.py
推荐：path_utils.py
推荐：image_normalization.py
推荐：retry_policy.py
```

（3）模块导入时不应执行网络请求、数据库访问、模型加载或主业务流程。

```python
# 不推荐：导入模块时立即执行昂贵操作
model = load_large_model()
records = fetch_remote_records()
```

（4）可执行模块应将主流程放入 `main()`。

```python
def main() -> None:
    ...


if __name__ == "__main__":
    main()
```

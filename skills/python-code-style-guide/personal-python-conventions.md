# 个人 Python 工程偏好

本文档记录个人在 Python 项目中的工程偏好，是《Python 代码风格指南》的补充，不重复其中已经明确规定的通用规则。

规则优先级如下。

1. 项目已有的明确约定
2. 本文档中的个人工程偏好
3. 《Python 代码风格指南》中的通用规则

项目因框架、兼容性或外部接口限制无法遵循本文档时，应优先保持项目内一致，并在必要处说明原因。

## 日志

程序运行状态、诊断信息和异常上下文统一使用 Python 标准库 `logging`，不得使用 `print()` 代替业务日志。

```python
import logging

logger = logging.getLogger(__name__)


def load_records() -> None:
    logger.info("Loading records")
```

日志调用遵守通用规范中的参数化日志和敏感信息保护要求。

```python
# 不推荐
logger.info(f"Loaded {record_count} records")

# 推荐
logger.info("Loaded %d records", record_count)
```

以下情况不属于使用 `print()` 代替日志。

- CLI 向标准输出返回正常结果
- CLI 向标准错误输出返回面向用户的错误提示
- 测试或交互式调试中的临时输出

库代码只创建模块级 logger，不主动配置根 logger；日志级别、输出格式和处理器由应用入口统一配置。

## 文件系统路径

Python 内部的本地文件系统路径统一使用 `pathlib.Path`，不使用字符串拼接或 `os.path` 组织路径。

```python
from pathlib import Path


def load_config(config_path: Path) -> str:
    return config_path.read_text(encoding="utf-8")
```

来自 CLI、环境变量和配置文件的字符串路径，应在进入业务逻辑时尽早转换为 `Path`。

```python
input_path = Path(args.input)
```

仅在第三方接口、序列化或协议边界要求字符串时，按需使用 `str(path)`。

URL、URI、对象存储键和其他不具有本地文件系统语义的标识符不应转换为 `Path`。

## 常量与 Magic Number

具有业务含义、需要解释、可能调整或跨位置重复使用的数字，不得以 Magic Number 的形式散落在代码中，应提取为命名常量、枚举成员或配置字段。

```python
# 不推荐
for attempt in range(3):
    ...

# 推荐
MAX_RETRY_COUNT = 3

for attempt in range(MAX_RETRY_COUNT):
    ...
```

常见的提取对象包括：

- 超时时间
- 重试次数
- 端口号
- 缓存大小
- 限流阈值
- 状态码和协议值
- 业务判断阈值

`0`、`1` 等自然边界、明确的索引、数学公式中的固有数字，以及局部且含义清楚的测试数据，可以直接使用。

## 配置对象

完成解析、默认值填充和校验后，业务逻辑内部的配置优先使用 `dataclass` 定义的类型化对象，并通过属性访问配置项，不使用多层字典传递稳定配置。

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    input_path: Path
    timeout_seconds: float
    max_retry_count: int
```

```python
# 不推荐
input_path = config["paths"]["input"]

# 推荐
input_path = config.input_path
```

配置对象默认优先使用 `frozen=True`，除非运行期间确实需要修改。

JSON、YAML、环境变量等外部原始配置可以在解析阶段暂时使用 `Mapping` 或 `dict`。字段集合动态变化、插件需要扩展字段或配置需要原样透传给第三方时，也可以保留映射结构。

本文所称“`dataclass` 风格”是指类型化字段和属性访问风格，不是 `typing.ClassVar` 声明的类变量。

## 命令行接口

一般工具通过命令行参数暴露用户接口，默认使用标准库 `argparse`，不手工解析 `sys.argv`。参数解析与业务逻辑应分离。

```python
import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(input_path=args.input)
```

常用且含义明确的可选参数同时提供长短选项，短选项写在前、长选项写在后，例如：

```text
-i, --input
-o, --output
-c, --config
-v, --verbose
```

低频参数、含义不清晰的参数或短选项存在冲突时，可以只提供长选项。位置参数不需要额外提供短选项。

CLI 参数名称使用小写字母和连字符；解析后的 Python 属性由 `argparse` 转换为下划线形式。

```python
parser.add_argument("--max-retries", type=int)
# 通过 args.max_retries 访问
```

# 导入

## 导入位置

导入语句放在模块文档字符串之后、模块常量和其他代码之前。

`from __future__` 导入应位于模块文档字符串之后、其他导入之前。

```python
"""Load and validate application configuration."""

from __future__ import annotations

from pathlib import Path
```

## 导入分组

导入按以下顺序分组，各组之间空一行。

1. Python 标准库
2. 第三方库
3. 当前项目代码

```python
import json
from pathlib import Path

import requests

from my_project.config import AppConfig
from my_project.storage import repository
```

## 导入形式

（1）普通 `import` 每行只导入一个模块。

```python
# 不推荐
import os, sys

# 推荐
import os
import sys
```

（2）避免通配符导入。

```python
# 不推荐
from models import *
```

通配符导入会隐藏名称来源，并干扰静态分析。

（3）通常优先使用绝对导入。包内确有需要时，可以使用明确的相对导入，但项目内必须统一。

（4）只有公认缩写或解决名称冲突时才使用别名。

```python
import numpy as np
import pandas as pd
```

不要为普通模块随意创造缩写。

## 公共接口

模块可以使用 `__all__` 明确声明公共接口。

```python
__all__ = [
    "ConfigError",
    "load_config",
]
```

未公开的函数、类和变量使用单前导下划线。

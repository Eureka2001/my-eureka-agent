# 日志

## 日志内容

日志应帮助定位事件，不应只是重复“发生错误”。

```python
# 不推荐
logger.error("Request failed")

# 推荐
logger.error(
    "Request failed: request_id=%s endpoint=%s",
    request_id,
    endpoint,
)
```

## 参数化日志

日志调用使用模板和参数，不要预先使用 f-string 拼接。

```python
# 不推荐
logger.info(f"Loaded {user_count} users")

# 推荐
logger.info("Loaded %d users", user_count)
```

这样可以推迟字符串格式化，并便于日志系统处理结构化参数。

## 敏感信息

日志不得记录以下信息。

- 密码
- 访问令牌
- 私钥
- 完整身份凭证
- 无必要的个人敏感信息

异常日志应保留必要上下文，但不要泄露敏感数据。

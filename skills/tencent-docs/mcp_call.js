#!/usr/bin/env node
/**
 * 腾讯文档 MCP 直连调用封装（零 npm 依赖，Node >= 14）
 *
 * CLI 用法:
 *   node mcp_call.js <tool_name> [args_json]
 *   成功: stdout 输出工具返回结果（对象序列化为 JSON，纯文本原样输出）
 *   失败: stderr 输出错误信息，exit 1
 *
 * 模块用法:
 *   const { callMcp } = require("./mcp_call.js");
 *   const result = await callMcp("manage.create_file", { title: "x" });
 *
 * Authorization token 取自环境变量 TENCENT_DOCS_TOKEN（厂商 frontmatter 约定的 primaryEnv）。
 * 响应兼容纯 JSON 与 SSE（text/event-stream）两种格式，自动从 JSON-RPC 信封解出工具结果。
 */
"use strict";

const https = require("https");

const MCP_URL = "https://docs.qq.com/openapi/mcp";

function unwrap(resp) {
  if (resp.error) {
    throw new Error("MCP error: " + JSON.stringify(resp.error));
  }
  const r = resp.result || {};
  if (r.isError) {
    throw new Error("tool error: " + JSON.stringify(r.structuredContent || r.content || {}));
  }
  if (r.structuredContent !== undefined && r.structuredContent !== null) {
    return r.structuredContent;
  }
  const t = r.content && r.content[0] && r.content[0].text;
  if (typeof t === "string") {
    try { return JSON.parse(t); } catch (e) { return t; }
  }
  throw new Error("empty result");
}

function callMcp(tool, argsObj) {
  return new Promise((resolve, reject) => {
    const token = process.env.TENCENT_DOCS_TOKEN;
    if (!token) {
      reject(new Error("TENCENT_DOCS_TOKEN not set"));
      return;
    }
    const body = JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: { name: tool, arguments: argsObj || {} },
    });
    const req = https.request(MCP_URL, {
      method: "POST",
      headers: {
        "Authorization": token,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Content-Length": Buffer.byteLength(body),
      },
      timeout: 120000,
    }, (res) => {
      let data = "";
      res.setEncoding("utf8");
      res.on("data", (c) => { data += c; });
      res.on("end", () => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error("HTTP " + res.statusCode + " " + String(data).slice(0, 300)));
          return;
        }
        let raw = data;
        if (/^\s*(event|data):/m.test(data)) {
          // SSE 帧：取最后一个 data: 行
          const lines = data.split(/\r?\n/).filter((l) => l.indexOf("data:") === 0);
          if (lines.length) raw = lines[lines.length - 1].slice(5).trim();
        }
        let resp;
        try {
          resp = JSON.parse(raw);
        } catch (e) {
          reject(new Error("invalid response: " + String(raw).slice(0, 300)));
          return;
        }
        try { resolve(unwrap(resp)); } catch (e) { reject(e); }
      });
    });
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(new Error("timeout")); });
    req.write(body);
    req.end();
  });
}

module.exports = { callMcp };

if (require.main === module) {
  const argv = process.argv.slice(2);
  const tool = argv[0];
  if (!tool) {
    console.error("usage: node mcp_call.js <tool_name> [args_json]");
    process.exit(1);
  }
  let args = {};
  if (argv[1] !== undefined) {
    try { args = JSON.parse(argv[1]); } catch (e) {
      console.error("invalid args json: " + argv[1]);
      process.exit(1);
    }
  }
  callMcp(tool, args).then((r) => {
    console.log(typeof r === "string" ? r : JSON.stringify(r));
  }).catch((e) => {
    console.error(String(e.message || e));
    process.exit(1);
  });
}

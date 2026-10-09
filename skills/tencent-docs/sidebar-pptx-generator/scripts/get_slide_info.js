#!/usr/bin/env node
/**
 * Inspect a Tencent Docs PPT and return compact JSON for LLM routing.
 *
 * Usage:
 *   node sidebar-pptx-generator/scripts/get_slide_info.js <file_url_or_id> [--file-id]
 *
 * Output:
 *   {"action":"write_design_md"|"proceed_next","reason":"...",...}
 *
 * 依赖: Node >= 14；Authorization token 取自环境变量 TENCENT_DOCS_TOKEN（厂商约定）。
 */
"use strict";

const { callMcp } = require("../../mcp_call.js");

async function main() {
  const argv = process.argv.slice(2);
  const input = argv[0];
  if (!input) {
    console.log("ERROR:missing_argument");
    process.exit(1);
  }
  const key = argv[1] === "--file-id" ? "file_id" : "file_url";
  const baseArgs = {};
  baseArgs[key] = input;

  const out = (o) => console.log(JSON.stringify(o));
  const fail = (msg) => { console.error(msg); process.exit(1); };

  let info;
  try {
    info = await callMcp("slide_get_info", baseArgs);
  } catch (e) {
    fail("ERROR:slide_get_info_failed - " + String(e.message || e));
  }

  const slideCount = Number(info.slide_count) || 0;
  const wPt = Number(info.w_pt) || 0;
  const hPt = Number(info.h_pt) || 0;

  // ── Permission check ──
  // 仅当"有尺寸但 0 页"时才可能缺 VIEW 权限。
  // 注：主端点未暴露 check_access 工具；调用失败按"无法判定"处理，落入后续空 PPT 分支。
  if (slideCount === 0 && wPt > 0 && hPt > 0) {
    const fileId = key === "file_id" ? input : String(input).replace(/.*\/([^/?#]+).*/, "$1");
    if (fileId) {
      try {
        const access = await callMcp("check_access", { file_id: fileId, actions: ["VIEW"] });
        const hasView = (access.granted_actions || []).indexOf("VIEW") !== -1;
        if (!hasView) {
          out({
            action: "ask_user", reason: "permission_denied",
            slide_count: slideCount, w_pt: wPt, h_pt: hPt, file_id: fileId,
            hint: "当前账号无 VIEW 权限，请分享文档或下载到本地后重试",
          });
          return;
        }
      } catch (e) { /* check_access 不可用：无法判定，继续 */ }
    }
  }

  if (slideCount === 0 || wPt === 0 || hPt === 0) {
    out({ action: "write_design_md", reason: "ppt_is_empty", slide_count: slideCount, w_pt: wPt, h_pt: hPt });
    return;
  }

  let contentPages = 0;
  for (let i = 0; i < slideCount; i++) {
    let page;
    try {
      page = await callMcp("slide_get_page_info", Object.assign({ page_index: i }, baseArgs));
    } catch (e) { continue; }

    const shapes = page.shapes || [];
    const hasContent = shapes.some((s) => String((s && s.text) || "").replace(/\s/g, "") !== "");
    if (hasContent) contentPages++;
  }

  if (contentPages === 0) {
    out({
      action: "write_design_md", reason: "ppt_content_is_empty",
      slide_count: slideCount, w_pt: wPt, h_pt: hPt, content_page_count: contentPages,
    });
    return;
  }

  let design;
  try {
    design = await callMcp("slide_get_design", baseArgs);
  } catch (e) {
    fail("ERROR:slide_get_design_failed - " + String(e.message || e));
  }

  const designExists = Boolean(design.exists);
  const designMd = design.design_md || "";

  if (!designExists || designMd === "" || designMd === '""') {
    out({
      action: "write_design_md", reason: "design_is_empty",
      slide_count: slideCount, w_pt: wPt, h_pt: hPt,
      content_page_count: contentPages, design_exists: designExists,
    });
    return;
  }

  out({
    action: "proceed_next", reason: "design_exists",
    slide_count: slideCount, w_pt: wPt, h_pt: hPt,
    content_page_count: contentPages, design_exists: designExists,
    design_md_length: designMd.length, updated_at: String(design.updated_at || "0"),
  });
}

main().catch((e) => {
  console.error(String((e && e.message) || e));
  process.exit(1);
});

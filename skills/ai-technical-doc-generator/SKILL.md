---
name: ai-technical-doc-generator
description: This skill should be used when the user asks to generate a deep technical document about an AI topic, paper, architecture, model, algorithm, engineering system, or interview-heavy concept. It produces a structured Chinese Markdown technical document with mechanism explanation, architecture tracing, mathematical intuition when appropriate, tensor or data-flow analysis, training and inference details, bottlenecks, engineering trade-offs, failure modes, evaluation design, written-exam angles, and interview follow-up questions. It is tailored to multimodal large models, VLMs, SFT, vLLM-style inference, 3D semantic mapping, zero-shot navigation, embodied AI, map and storefront-sign understanding, dense visual features, and 3D Gaussian Splatting. For purely podcast-first school-recruiting drill briefs, prefer the mobile-podcast-ai-interview-briefing skill; this skill can additionally generate a written “面试与笔试特训附录” when the user wants a long-form document plus recruiting preparation.
description_zh: AI重型技术文档
description_en: AI Technical Doc Generator
disable: false
agent_created: true
---

# ai-technical-doc-generator

## When to use
Trigger this skill when the user asks for:
- A technical document, 技术文档, 深度报告, architecture note, paper note, design doc, or system analysis about an AI topic.
- A long-form explanation of a model or method such as Transformer, DINO, CLIP, SAM, LoRA, Qwen-VL, RAG, RLHF, diffusion, vLLM, KV Cache, FlashAttention, 3D Gaussian Splatting, semantic mapping, or zero-shot navigation.
- A document suitable for saving as Markdown, sharing with collaborators, preparing interviews, written-exam review, or turning into later slides or podcasts.
- A comparison of methods where the user needs engineering-level reasoning rather than a shallow summary.
- A long-form school-recruiting preparation document that must include interview traps, written-exam derivation points, complexity analysis, and engineering failure cases.

Routing rule:
- If the user mainly wants a short, TTS-first Doubao podcast briefing for commuting, use `mobile-podcast-ai-interview-briefing` instead of this skill.
- If the user wants a heavy Markdown document that can later be converted into podcast material, use this skill and add a recruiting-focused appendix.

## Steps
1. Determine the document mode:
   - If the user requests a file, create a Markdown document in the workspace and deliver it.
   - If the user asks for inline output, write the document directly in the response.
   - If the user provides papers or excerpts, treat them as primary sources and separate source-grounded claims from inferred engineering analysis.
2. Clarify or infer the target depth:
   - Interview document: emphasize core principle, tensor flow, bottlenecks, killer questions, and concise examples.
   - Written-exam document: emphasize derivation intuition, objective functions, complexity, memory usage, boundary cases, and common multiple-choice or short-answer traps.
   - Podcast-adapted document: keep the full technical-document structure, but add an oral-review appendix and avoid visual-only tables or dense symbolic notation in that appendix.
   - Research document: emphasize problem formulation, related work map, novelty, assumptions, limitations, and experiments.
   - Engineering document: emphasize data pipeline, training or inference pipeline, serving constraints, memory, latency, observability, failure modes, and rollback strategy.
   - If unspecified, use a hybrid mode that serves both research understanding and big-tech algorithm interviews.
3. Produce the document using this default structure:

   # [技术主题] 技术文档

   ## 0. 一句话定位
   Define what the technique is, what problem it solves, and why it matters.

   ## 1. 背景与问题设定
   Explain the historical motivation, predecessor limitations, and the exact technical pain point.

   ## 2. 核心机制总览
   Explain the architecture and key modules at a systems level before diving into details.

   ## 3. 数据流、张量流与信息流
   Trace inputs, features, projections, attention or fusion, losses, outputs, and where information is compressed, aligned, or discarded. Use symbolic notation only when useful for a written technical document; if the user asks for podcast-friendly output, switch to spoken Chinese descriptions and avoid formulas.

   ## 4. 训练目标与优化行为
   Explain objectives, gradients or optimization intuition, stability issues, negative sampling or supervision choices, and what the model is actually encouraged to learn.

   ## 5. 推理、部署与系统瓶颈
   Analyze memory, compute, bandwidth, latency, batching, cache behavior, quantization, parallelism, and monitoring concerns.

   ## 6. 工程权衡与帕累托边界
   Discuss accuracy, generalization, parameter efficiency, data cost, latency, robustness, and maintainability.

   ## 7. 与用户场景的结合
   Connect the topic to multimodal large models, map base imagery, storefront-sign context, dense feature extraction, SFT, POI topology, zero-shot navigation, 3D semantic mapping, embodied AI, or 3D Gaussian Splatting when relevant.

   ## 8. 常见误区与失败模式
   Explain misconceptions, edge cases, training collapse, evaluation leakage, domain shift, annotation noise, and serving instability.

   ## 9. 实验与评估设计
   Provide datasets, metrics, baselines, ablations, stress tests, and qualitative visualization ideas.

   ## 10. 校招面试与笔试特训
   Provide interviewer follow-up chains, written-exam traps, derivation checkpoints, complexity and memory analysis, and short-answer templates. Explicitly mark what must be memorized, what must be understood, and what can be used as an engineering story.

   ## 11. 面试官追问清单
   Provide progressively harder questions and answer directions, especially questions that distinguish memorization from implementation understanding.

   ## 12. 播客化复习附录
   When the user wants podcast reuse, provide a compact oral-review appendix with no code, no formula blocks, and no dense symbolic tensor shapes. Write it as spoken Chinese that can be pasted into Doubao or converted into a separate `mobile-podcast-ai-interview-briefing` output.

   ## 13. 总结与行动建议
   End with what to remember, what to test first, and how to reuse the knowledge in research or interviews.

4. Use a direct, high-density Chinese style. Prefer layered headings, bullet points, and explicit trade-offs. Avoid empty academic phrasing.
5. When the topic is related to the user’s projects, include practical examples around VLM storefront-sign recognition, image quality scoring, coordinate rendering, POI topology, vLLM plus Flask inference serving, Qwen-style multimodal SFT, or 3DGS rendering integration.
6. If current facts, paper details, or benchmark numbers matter and are not provided, use web research when appropriate. Cite sources only when actually verified. Never invent paper results, leaderboard rankings, or company claims.
7. If generating a file, use a clean filename pattern such as `AI_技术文档_[技术主题]_[日期].md` unless the user specifies another name.

## Pitfalls
- Do not write a generic encyclopedia article. Always include mechanism, bottleneck, engineering trade-off, and evaluation implications.
- Do not hide uncertainty. Mark unclear claims as assumptions or hypotheses.
- Do not overuse formulas when the user needs oral review; switch style based on the target medium.
- Do not let the heavy document replace the dedicated podcast skill when the user asks for commuting audio material only.
- Do not omit written-exam angles such as complexity, memory, objective-function intuition, and boundary cases when the user mentions 校招, 面试, 笔试, or 八股.
- Do not include code unless the user explicitly asks for implementation snippets.
- Do not cite unverified sources or fabricate benchmark numbers.
- Do not ignore system-level failure modes; for the user, deployment stability and debugging stories are part of the value.

## Verification
Before finalizing, verify that:
- The document has a clear target mode and complete structure.
- The core mechanism can be understood without relying on buzzwords.
- Data flow or tensor flow is explicitly traced.
- Bottlenecks and trade-offs are concrete rather than decorative.
- 校招面试与笔试 content is present when the user asks for recruiting preparation.
- Podcast-oriented content is routed to `mobile-podcast-ai-interview-briefing` for short TTS-first briefs, or included as a clear appendix for long-form documents.
- The user’s multimodal, 3D mapping, zero-shot navigation, and engineering background is leveraged when relevant.
- Any claims requiring freshness or citations are either sourced or clearly labeled as assumptions.

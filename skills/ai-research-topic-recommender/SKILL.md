---
name: ai-research-topic-recommender
description: This skill should be used when the user asks for AI research topic recommendations, thesis or paper directions, project ideas, research-roadmap choices, or topic prioritization. It is tailored for a Chinese AI algorithm researcher preparing autumn recruiting while working on multimodal large models, 3D semantic mapping, zero-shot navigation, embodied AI, storefront-sign and map-scene understanding, SFT, inference serving, and 3D Gaussian Splatting. It produces ranked, actionable, Pareto-aware research topics with novelty, feasibility, data needs, interview value, and next-step validation plans.
description_zh: AI研究选题推荐
description_en: AI Research Topic Recommender
disable: false
agent_created: true
---

# ai-research-topic-recommender

## When to use
Trigger this skill when the user asks for any of the following:
- Recommend research topics, paper ideas, thesis directions, project ideas, or publishable angles.
- Choose between multiple AI directions under limited time, data, compute, or advisor constraints.
- Turn a vague interest such as multimodal mapping, embodied AI, VLM, zero-shot navigation, LoRA, RAG, or 3DGS into concrete research questions.
- Build a topic roadmap that balances research value, engineering feasibility, and autumn-recruiting interview value.

## Steps
1. Extract the user’s constraints:
   - Time budget, deadline, compute budget, available data, advisor or lab direction, target venue or internal deliverable, and whether the goal is paper output, engineering demo, interview moat, or thesis progress.
   - If constraints are missing, infer conservative defaults from the user profile: limited time, high pressure from internship and lab work, preference for reusable engineering assets, multimodal and 3D embodied-intelligence background, and Chinese big-tech algorithm interview preparation.
2. Build a candidate pool across three layers:
   - Safe layer: incremental but executable topics that can be finished with existing data and models.
   - Differentiation layer: topics that connect multimodal large models with map understanding, storefront-sign context, dense visual features, 3D semantic mapping, zero-shot navigation, or 3D Gaussian Splatting.
   - High-risk layer: topics with stronger novelty but higher uncertainty in data, evaluation, system stability, or reproduction cost.
3. Score each topic using five dimensions:
   - Novelty and research taste.
   - Feasibility under the user’s current time and compute constraints.
   - Data availability and annotation cost.
   - Engineering reusability and demo value.
   - Interview value for multimodal and large-model algorithm roles.
4. Prefer topics with a clear “minimum publishable or demoable unit”:
   - One concrete hypothesis.
   - One available baseline.
   - One measurable metric.
   - One ablation that can prove the key claim.
   - One failure case that can be turned into an interview story.
5. Output in Chinese with this structure:

   ## 研究选题推荐：[任务或方向名称]

   ### 1. 总体判断
   Summarize the recommended direction, why it fits the user now, and what trade-off it makes.

   ### 2. 选题候选池
   Provide three to seven ranked topics. For each topic include: 核心问题, 创新点, 可行性, 数据与算力需求, 面试价值, 最大风险, 第一周验证动作.

   ### 3. 最推荐的主线
   Pick one primary topic and explain why it dominates the others under Pareto constraints.

   ### 4. 备选与降级路线
   Provide fallback versions if time, data, or compute collapses.

   ### 5. 下一步执行清单
   Provide concrete next actions for literature reading, data inspection, baseline reproduction, evaluation design, and demo planning.

6. If the user asks for “最新” or current SOTA, use web research from reliable sources when available, but do not fabricate citations. Clearly distinguish verified literature from strategic speculation.

## Pitfalls
- Do not recommend broad buzzword topics without a testable hypothesis.
- Do not optimize only for paper novelty while ignoring data, compute, and user time pressure.
- Do not ignore the user’s personal moat in multimodal large models, 3D mapping, zero-shot navigation, embodied AI, and map-scene understanding.
- Do not produce a reading list without explaining why each item changes the research decision.
- Do not over-promise publishability. Separate “can make a demo”, “can support a thesis section”, and “may become a paper”.

## Verification
Before finalizing, verify that:
- At least one recommended topic is executable with limited time and data.
- Each topic has a concrete hypothesis, metric, baseline, and risk.
- The top recommendation explicitly explains the Pareto trade-off.
- The output helps both research progress and autumn-recruiting interview storytelling.

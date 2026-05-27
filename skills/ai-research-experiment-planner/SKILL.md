---
name: ai-research-experiment-planner
description: This skill should be used when the user has selected or is considering an AI research topic and wants to turn it into an executable experiment plan. It converts a topic, paper idea, thesis direction, or model-improvement proposal into hypotheses, baselines, datasets, metrics, ablations, implementation stages, compute and memory risks, failure diagnostics, and a staged roadmap. It is tailored to multimodal large models, VLM SFT, map-scene and storefront-sign understanding, POI topology, 3D semantic mapping, zero-shot navigation, embodied AI, vLLM-style inference systems, and 3D Gaussian Splatting engineering.
description_zh: AI研究实验规划
description_en: AI Research Experiment Planner
disable: false
agent_created: true
---

# ai-research-experiment-planner

## When to use
Trigger this skill when the user asks to:
- Turn a research topic into an experiment plan, implementation roadmap, ablation plan, or paper-proof plan.
- Decide baselines, datasets, metrics, and minimal viable experiments for an AI idea.
- Debug why a research experiment is not convincing, not reproducible, unstable, too expensive, or hard to evaluate.
- Build a plan for multimodal SFT, VLM evaluation, zero-shot navigation, 3D mapping, embodied AI, 3D Gaussian Splatting, POI topology, or inference-system experiments.

## Steps
1. Restate the research claim in one sentence:
   - Identify the independent variable, expected effect, target scenario, and why the claim is non-trivial.
   - If the topic is vague, convert it into two or three testable hypotheses and rank them by feasibility.
2. Define the minimum viable experiment:
   - Choose the smallest dataset slice, baseline, metric, and ablation that can validate or falsify the central claim.
   - Prefer experiments that can fail quickly and reveal useful information.
3. Specify baselines:
   - Include a naive baseline, a strong known baseline, and the user’s proposed method.
   - For multimodal or mapping tasks, include modality-drop, prompt-only, fine-tuning, retrieval-enhanced, and geometry-aware variants when relevant.
4. Specify datasets and data protocol:
   - Define train, validation, and test separation.
   - Identify annotation requirements, leakage risks, domain shift, long-tail cases, and negative examples.
   - For map, storefront-sign, POI, navigation, or 3D tasks, explicitly address geographic split, scene split, time split, camera distribution, and occlusion or blur cases when applicable.
5. Specify metrics and evaluation logic:
   - Include primary metric, secondary metric, robustness metric, efficiency metric, and qualitative inspection.
   - Explain what each metric can and cannot prove.
6. Design ablations:
   - Remove or vary one component at a time.
   - Include data scale, model size, adapter rank, context length, retrieval source, geometric prior, rendering quality, and inference batching ablations when relevant.
7. Identify engineering risks:
   - Training instability, GPU memory pressure, data loader bottlenecks, annotation noise, prompt leakage, evaluation leakage, serving latency, cache pressure, quantization loss, and rendering pipeline instability.
   - Provide diagnosis signals and fallback plans.
8. Output in Chinese using this structure:

   ## 实验规划：[研究话题]

   ### 1. 核心假设
   State the main hypothesis and why it matters.

   ### 2. 最小可验证实验
   Describe the smallest experiment that can validate or kill the idea.

   ### 3. 数据、基线与指标
   Provide the dataset protocol, baselines, metrics, and expected observations.

   ### 4. 消融实验矩阵
   List the ablations and what each ablation proves.

   ### 5. 工程风险与排查路径
   Provide likely failure modes, logs or symptoms to inspect, and fallback strategies.

   ### 6. 阶段性路线图
   Provide a staged plan: baseline reproduction, first improvement, ablation, stress test, qualitative analysis, final write-up.

   ### 7. 论文或汇报卖点
   Explain how to package the results into a paper section, lab report, interview story, or demo narrative.

9. If the user gives logs, metrics, or failed results, diagnose first, then update the experiment plan. Do not blindly propose new experiments before explaining current evidence.

## Pitfalls
- Do not create a huge plan that cannot be executed under the user’s time pressure.
- Do not list metrics without explaining what decision each metric supports.
- Do not let the proposed method only beat a weak baseline.
- Do not ignore data leakage, geographic split, scene bias, or evaluation set contamination.
- Do not treat qualitative visualization as decoration; use it to explain failure modes and model behavior.
- Do not skip fallback routes. Research plans must survive missing data, weak GPU availability, unstable training, or negative results.

## Verification
Before finalizing, verify that:
- The core hypothesis is falsifiable.
- The minimum viable experiment is small enough to run quickly.
- Baselines include both weak and strong comparisons.
- Metrics connect to the research claim.
- Ablations isolate causal factors.
- Engineering risks include diagnosis and fallback steps.
- The plan can become a paper section, lab update, or interview story.

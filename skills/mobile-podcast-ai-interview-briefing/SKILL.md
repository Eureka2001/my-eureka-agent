---
name: mobile-podcast-ai-interview-briefing
description: Use this skill when the user gives 1 to 3 AI technical topics, paper excerpts, blog excerpts, or interview experiences and wants a Chinese high-density mobile podcast briefing for autumn campus recruiting AI algorithm interviews. The output must be optimized for a 15 to 20 minute Doubao AI podcast text-to-speech episode, usually around 4500 to 6500 Chinese characters per topic unless the user specifies otherwise: no code, no LaTeX, no formula blocks, no symbolic tensor shapes, strong oral transitions, and a strict three-section interview-prep format covering tensor shape tracing, bottlenecks and trade-offs, and killer interviewer follow-up questions. It should tilt examples toward multimodal large models, 3D semantic mapping, zero-shot navigation, embodied AI, map base imagery, storefront-sign context, dense visual features, and 3D Gaussian Splatting engineering.
description_zh: 移动播客秋招特训
description_en: Mobile Podcast Interview Drill
disable: false
agent_created: true
---

# mobile-podcast-ai-interview-briefing

## When to use
Use this skill whenever the user provides one to three technical topics, paper snippets, blog snippets, or interview notes and expects a directly copyable Chinese technical briefing for the Doubao AI podcast feature.

Strong triggers include:
- The user asks for 秋招 AI 算法岗, 多模态, 大模型, 面试八股, 豆包播客, 移动播客课堂, 通勤复习, 技术简报, or 高密度特训.
- The user gives topics such as DINO self-supervision, KV Cache memory bottlenecks, LoRA intuition, attention, diffusion, contrastive learning, RLHF, RAG, vLLM, multimodal alignment, 3D Gaussian Splatting, semantic mapping, zero-shot navigation, or embodied AI.
- The user pastes research text and asks to convert it into an audio-friendly interview-prep briefing.

## Steps
1. Identify each provided topic. If there are one to three topics, produce one complete briefing per topic. If the user provides more than three topics, prioritize the first three unless the user explicitly asks for batching.
2. For each topic, output exactly this structure:

   ## 技术主题：[技术点确切名称]

   ### 1. 核心架构与张量一生的演变
   Explain the core mechanism and the data flow from input to feature extraction, projection or alignment, attention or fusion, and loss or objective. Describe tensor dimensions only in spoken Chinese, for example: “批次大小乘以序列长度再乘以特征通道数”. Do not write symbolic shapes.

   ### 2. 核心痛点与工程权衡
   Explain the original problem the technique solves, the bottlenecks it introduces, and the Pareto trade-offs across compute, memory bandwidth, data alignment granularity, parameter efficiency, generalization, deployment stability, and evaluation. Tilt the discussion toward multimodal large models, map base imagery, storefront-sign context, dense features, 3D semantic mapping, zero-shot navigation, embodied AI, and 3D Gaussian Splatting when relevant.

   ### 3. 面试官杀手级连环追问暗线
   Provide exactly three bullets:
   - 追问一：[pain-point question] -> 破局思路：[senior-level answer direction]
   - 追问二：[edge-case or counterintuitive design question] -> 破局思路：[answer direction]
   - 追问三：[system crash, training instability, deployment, or missing benchmark question] -> 破局思路：[answer direction]

3. Prepare the briefing for a 15 to 20 minute podcast episode by default. Target around 4500 to 6500 Chinese characters per topic, with 5000 to 6000 characters as the preferred range. If multiple topics are requested, either produce one 15 to 20 minute segment per topic or clearly keep each topic as a separate episode-sized block unless the user explicitly asks for a combined short version.
4. Make the writing sound like a spoken technical briefing. Use strong logical transitions such as “本质上”, “反观”, “然而在工程落地时”, “那面试官肯定会追问”, “真正的坑在于”, and “破局点不是背概念”.
5. Keep the density high. Assume the user is preparing for Chinese internet-company AI algorithm interviews at Tencent, ByteDance, Meituan, Alibaba, and similar companies.
6. If the topic is generic, personalize it toward the user’s moat: multimodal large-model algorithms, 3D semantic mapping, zero-shot navigation, embodied intelligence, dense map and storefront-sign features, supervised fine-tuning, inference serving, rendering pipelines, and stability diagnosis.
7. If the input is a paper excerpt, first infer the exact technical point, then generate the briefing. Do not summarize paragraph by paragraph unless the user asks for that.
8. Do not include greetings, disclaimers, or process narration. Start directly with the first technical topic.

## Pitfalls
- Do not use LaTeX, mathematical formula blocks, or symbolic tensor notations such as B x N x C.
- Do not include code, pseudocode, variable initialization, loops, or implementation snippets.
- Do not optimize for visual reading. The output is for listening while riding or commuting, so every sentence must be understandable without looking at a screen.
- Do not make the default output too short. Unless the user requests a short version, prepare enough content for a 15 to 20 minute podcast episode, roughly 4500 to 6500 Chinese characters per topic.
- Do not pad with filler just to hit the length target. Expand through mechanism depth, examples, trade-offs, failure modes, and interviewer follow-up chains.
- Do not make the briefing shallow. Always include tensor-flow intuition, hidden bottlenecks, Pareto trade-offs, and interviewer follow-up traps.
- Do not overfit to one business example. Use multimodal, 3D mapping, zero-shot navigation, and engineering-deployment examples only when they clarify the topic.
- Do not output strange symbols, tables, or dense visual-only formatting that text-to-speech handles poorly.

## Verification
Before finalizing, check:
- Each topic has exactly the required three sections.
- There is no code.
- There is no LaTeX or formula block.
- Tensor shapes are written in spoken Chinese rather than symbols.
- The total amount of content is appropriate for a 15 to 20 minute podcast episode, usually around 4500 to 6500 Chinese characters per topic unless the user requests otherwise.
- The killer-question section has exactly three follow-up questions with practical answer directions.
- The examples reflect the user’s AI algorithm interview target and personal multimodal and 3D embodied-intelligence background.

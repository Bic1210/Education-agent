# 任务9-10-11 合并 README

这三个任务是一条连续链路，不是三件互相独立的小任务：

- 任务9：把抽取 Prompt 从“能跑”迭代到“能用”
- 任务10：把当前可用 Prompt 放到 15 本书上做批量抽取
- 任务11：对任务10产出的实体做跨 chunk、跨书、跨语言去重合并

这一阶段实际完成的是一套从 Prompt 设计验证、批量执行，到后处理合并的完整工作流。所有相关代码、round 记录、结果文件和交接文档都统一收在 `test_prompt/` 目录下。

## 任务9：Prompt 迭代优化与评审闭环

任务9不是简单“改几句话”，而是把 Prompt 迭代流程工程化。

### 已完成内容

1. 基于任务8的人工评估结果做问题归纳  
前面先对两本书、30 个 chunk 的实体和关系抽取结果做了人工评估，并形成了结构化问题总结。

评估汇总结果：

- 总评估条目：`632` 条
- 合理：`549` 条，占 `86.9%`
- 有问题：`83` 条，占 `13.1%`

重点识别出的问题包括：

- 跨 chunk 重复提取同一实体
- 定义空洞或定义错误
- 冗余/过于工具化的实体
- 实体类型标注错误
- 关系类型错误
- 关系方向错误
- 评测维度误作节点

对应材料：

- [task8.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task8.md:1)
- [评估总结.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/评估总结.md:1)
- `test_prompt/eval_report_08_scored.csv`

2. 完成 `v2 -> v3 -> v4` 三轮 Prompt 迭代  
每一轮都围绕高频错误做定向修正，例如：

- 收紧实体准入条件
- 禁止把评测指标、性质、子属性抽成实体
- 收紧关系触发条件，避免同段全连接
- 强化 `包含` 关系方向约束
- 区分 `concept / algorithm / tool`
- 提高 definition 的信息密度，避免空泛定义

核心文件：

- [prompt_v2.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_v2.py:1)
- [prompt_v3.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_v3.py:1)
- [prompt_v4.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_v4.py:1)
- [prompt_registry.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_registry.py:1)

3. 建立复跑与二次评审闭环  
任务9不只是改 Prompt，还配套实现了复跑和评审工具：

- 抽取复跑脚本：[run_prompt_eval_v2.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_prompt_eval_v2.py:1)
- 评审 Prompt：[review_prompt_v1.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/review_prompt_v1.py:1)
- 评审脚本：[run_review_assistant.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_review_assistant.py:1)

这一步实现了：

- 固定样本复跑
- 不同 Prompt 版本对比
- 二次评审
- 问题归档

4. 沉淀 round 记录与执行模板  
为了让后续同学能继续接手，不只是留代码，还补了执行模板和逐轮记录：

- [task9_prompt_iteration.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task9_prompt_iteration.md:1)
- [task9_execution_template.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task9_execution_template.md:1)
- [round_01_v2_review.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/rounds/round_01_v2_review.md:1)
- [round_02_v3_review.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/rounds/round_02_v3_review.md:1)
- [round_03_v4_review.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/rounds/round_03_v4_review.md:1)
- [task9_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task9_README.md:1)

### 当前结论

- 当前默认可用版本是 `prompt_v4`
- 任务10和任务11都在这个基线上继续推进
- 任务9已完成迭代流程与可用基线沉淀
- 但质量还没有完全封板

一句话总结：

> 任务9完成了 Prompt 的问题分析、三轮迭代、复跑评审脚本和 round 记录沉淀，把“Prompt 调整”变成了一套可复用流程。

## 任务10：15本书批量抽取与工程验收

任务10做的是把任务9的 Prompt 真正放到大规模数据上跑通，而且不是一次性脚本，而是完整 harness。

### 已完成内容

1. 开发批量抽取脚本  
核心脚本：

- [run_batch_extraction.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_batch_extraction.py:1)

这个脚本支持：

- 多书批量处理
- chunk 级别持续落盘
- summary / manifest 持续更新
- 断点续跑
- 失败重试
- 按书或按 chunk 限制批次范围

相关说明文档：

- [task10_batch_harness.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_batch_harness.md:1)
- [task10_harness_workflow.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_harness_workflow.md:1)
- [task10_issue_ledger.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_issue_ledger.md:1)

2. 从 smoke test 推进到全量 15 本  
任务10不是直接上全量，而是分阶段推进：

- 先做 smoke test
- 再做前 10 本试跑
- 再补跑后 5 本
- 最后做全量合并、去重和验收

相关 round 记录：

- [round_00_batch_harness_setup.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_rounds/round_00_batch_harness_setup.md:1)
- [round_01_first10_trial.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_rounds/round_01_first10_trial.md:1)

3. 处理中途暴露的工程问题  
在批量跑过程中，任务10还解决了实际工程问题：

- 修复了续跑时回到错误断点的问题
- 给 `run_batch_extraction.py` 增加了 batch 范围校验
- 处理了 `connection error` 导致的失败 chunk 补跑
- 清零了 `first10` 中的残余失败项
- 完成了 `remaining5` 的续跑和去重清洗

4. 完成最终统计与验收  
最终统一口径为：

- 覆盖书本：`15/15`
- 唯一 chunk：`2501/2501`
- `remaining_error_keys = 0`

最终关键产物包括：

- [batch_extract_batch_v4_all15_deduped.jsonl](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_all15_deduped.jsonl)
- [batch_extract_batch_v4_all15_final_stats.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_all15_final_stats.json:1)
- [task10_acceptance_report.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/task10_acceptance_report.md:1)
- [task10_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_README.md:1)

### 当前结论

这里要分开两个口径：

- 工程口径：通过
- 质量口径：条件通过

原因不是工程没做完，而是任务9中的 Prompt 抽样复审还存在 `revise/reject`，所以不能把“15 本书全量跑完”直接写成“知识抽取质量完全达标”。

一句话总结：

> 任务10完成了 15 本书、2501 个唯一 chunk 的批量抽取工程化落地，跑通了续跑、补跑、去重和验收流程。

## 任务11：实体去重、跨书合并与后处理系统

任务11做的是任务10之后的全局后处理。这个工作量实际很大，因为它不是字符串去重，而是在做知识节点归一。

### 已完成内容

1. 明确任务11定位  
任务8和任务9里已经发现：Prompt 无法解决跨 chunk 和跨书重复问题。

所以任务11明确采用独立 harness 处理：

- 不改 Prompt
- 不回写任务10原始结果
- 在批后处理阶段做实体合并

2. 实现实体合并 harness  
核心脚本：

- [run_entity_merge_harness.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_entity_merge_harness.py:1)

说明文档：

- [task11_entity_merge_harness.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_entity_merge_harness.md:1)

它不是简单词表替换，而是一个三段式流程：

- 召回
- 评分筛选
- 人工兜底

3. 多轮迭代与策略升级  
任务11不是一版成型，而是经过多轮 round 逐步收敛：

- [round_01_all15_merge_v1.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_rounds/round_01_all15_merge_v1.md:1)
- [round_02_all15_merge_v2.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_rounds/round_02_all15_merge_v2.md:1)
- [round_03_all15_merge_v3.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_rounds/round_03_all15_merge_v3.md:1)
- [round_04_all15_merge_v4.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_rounds/round_04_all15_merge_v4.md:1)
- [round_05_all15_merge_v5.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_rounds/round_05_all15_merge_v5.md:1)
- [round_06_all15_merge_v6.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_rounds/round_06_all15_merge_v6.md:1)
- [round_07_all15_merge_v7.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_rounds/round_07_all15_merge_v7.md:1)

在这些 round 中，逐步加入了：

- 表面规范化
- 单复数变体合并
- 括号别名识别
- seed alias
- head word / token overlap / definition overlap
- `type / role gate`
- recall backlog
- board 化审计输出

4. 处理歧义缩写与误并控制  
任务11里的关键难点之一是缩写歧义，例如 `ML`。

并不是所有 `ML` 都能自动等于 `machine learning`，因为统计语境里也可能代表 `maximum likelihood`。所以这一步专门沉淀了：

- [entity_merge_seed_aliases.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/entity_merge_seed_aliases.json:1)
- [entity_merge_ambiguous_acronyms.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/entity_merge_ambiguous_acronyms.json:1)

当前规则是：

- 高置信 alias 可以合并
- 歧义缩写只进候选，不自动 merge

5. 完成当前稳定基线  
当前稳定基线是 `round_07_all15_merge_v7`。

主要结果：

- 输入 mention：`13363`
- 唯一 entity form：`9761`
- candidate pairs：`524`
- 自动 merge：`453`
- uncertain：`69`
- blocked：`2`
- 合并后 cluster：`9354`
- 节点净减少：`407`

已经能稳定处理的包括：

- 大小写变体
- 空格/连字符变体
- 单复数变体
- 显式别名
- 部分中英对照

例如可以合并：

- `机器学习 / machine learning / Machine learning`
- `主成分分析 / principal component analysis / PCA`
- `奇异值分解 / singular value decomposition / SVD`

同时也能拦住高风险误并：

- `ML`
- `machine learning ROM`
- `correlation coefficient`
- `Controllability matrix`
- `conversion rate`

6. 输出审计文件与交接材料  
任务11不仅有 summary，还输出了板块化结果，方便人工检查：

- [round_07_all15_merge_v7_summary.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_summary.json:1)
- [round_07_all15_merge_v7_clusters.jsonl](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_clusters.jsonl)
- [surface_variants](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_board_surface_variants.jsonl)
- [inflection_variants](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_board_inflection_variants.jsonl)
- [explicit_aliases](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_board_explicit_aliases.jsonl)
- [blocked_by_role](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_board_blocked_by_role.jsonl)
- [recall_backlog](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_recall_backlog.jsonl)
- [task11_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_README.md:1)

一句话总结：

> 任务11完成了从任务10抽取结果出发的全局实体去重与跨书合并系统，当前基线以低误并优先，已经具备继续扩召回的能力。

## 整体阶段性成果

如果整体对外汇报，可以这样概括：

这一阶段在 `test_prompt/` 下完成了从 Prompt 迭代、批量抽取到实体合并的完整实验链路建设。

- 任务9完成了 Prompt 的问题分析、三轮优化、固定样本复跑和评审闭环，形成了当前默认基线 `v4`
- 任务10在此基础上完成了 15 本书、2501 个唯一 chunk 的批量抽取、续跑补跑和最终验收
- 任务11进一步对全量抽取结果进行了跨 chunk、跨书、跨语言的实体合并，建立了保守可靠的 merge harness，并形成了当前 `round_07_all15_merge_v7` 的合并基线

## 推荐查看顺序

如果只想先看一份文件，优先看本文。

如果要继续深挖，建议按这个顺序：

1. [task9_10_11_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task9_10_11_README.md:1)
2. [task9_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task9_README.md:1)
3. [task10_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_README.md:1)
4. [task11_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_README.md:1)

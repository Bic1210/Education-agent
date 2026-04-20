# 任务11：实体合并 Harness

任务11不改抽取 prompt，不回写任务10 的 batch 结果，而是在 `test_prompt/` 下新增一个批后处理 harness，专门处理：

- 跨 chunk 重复
- 跨书别名归一
- 跨语言同义项合并
- 高风险误合并审计

## 核心原则

1. 宁可少合，不要错合
- 自动合并只允许高置信信号
- 低置信样本全部进入待审层

2. 词库不是主方案
- curated alias seed 只是一个高精度信号
- 不做“大词库一把梭”的粗暴并法
- 像 `ML` 这种歧义缩写只进候选层，不做全局自动 merge
- `ML`、`M.L.`、`M-L` 这类缩写变体也按歧义缩写处理

3. prompt 不解决跨书合并
- 任务10已经明确：跨书别名归一、全局合并、节点标准化留给任务11

4. 不是“一个都不能拉下”的纯规则系统
- 任务11采用：`召回 -> 评分筛选 -> 人工兜底`
- 自动 merge 只负责高置信等价项
- 不能安全自动 merge 的候选进入 review / backlog

## Harness 结构

### 1. 输入层
- 输入文件默认使用：
  `test_prompt/results/batches/batch_extract_batch_v4_all15_deduped.jsonl`

### 2. 实体 form 层
- 先把每个 chunk 的实体 mention 拉平
- 再聚合成唯一 `form = (name, type)` 节点
- 记录：
  - mention 次数
  - 覆盖书本数
  - 语言
  - 样例来源
  - top definitions

### 3. 候选层
- 只生成高精度候选：
  - 表面规范化一致
  - curated seed alias 命中
  - 括号别名
  - acronym-longform
- 弱召回信号：
  - head word
  - token overlap
  - definition overlap
  - surface containment

### 4. 决策层
- `merge`
- `uncertain`
- `keep_separate`（由 type / role gate 硬拦截）

当前决策逻辑：

- 先累计多信号 score
- 再做 `type / role gate`
- 最后分成：
  - `merge`
  - `uncertain`
  - `keep_separate`

### 5. 输出层
- `raw_entities`
- `entity_forms`
- `candidate_pairs`
- `merge_decisions`
- `clusters`
- `review_samples`
- `summary`
- `round report`

## 当前脚本

- [run_entity_merge_harness.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_entity_merge_harness.py:1)

## 运行方式

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
python3 test_prompt/run_entity_merge_harness.py
```

预览模式：

```bash
python3 test_prompt/run_entity_merge_harness.py --dry-run
```

## 结果目录

- `test_prompt/results/entity_merge/`
- `test_prompt/task11_rounds/`

## 当前板块

- `surface_variants`
- `inflection_variants`
- `explicit_aliases`
- `ambiguous_acronyms`
- `blocked_by_role`
- `recall_review`
- `risky_review`

## 当前推荐工作流

1. 跑一轮全量 candidate generation
2. 看 `review_samples`
3. 先人工检查高风险 uncertain
4. 扩充 seed alias 或规则
5. 再跑下一轮
6. 比较 cluster 数、误并样本、待审样本是否收敛

## 达标判断

- 高风险簇抽检不出现系统性误并
- 节点数明显下降
- 核心概念没有被吞并
- 剩余问题主要是“边界模糊”，而不是明显错合

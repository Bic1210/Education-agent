# 任务11 README：实体去重与跨书合并

任务11的目标是：在任务10的批量抽取结果之上，做批后处理的实体合并，解决跨 chunk、跨书、跨语言的重复实体问题。

这一步不改 Prompt，不回写任务10原始抽取结果，而是在 `test_prompt/` 下单独运行一个 merge harness。

## 当前结论

- 当前基线版本：`round_07_all15_merge_v7`
- 任务11当前状态：**已完成可运行的保守版合并 harness**
- 任务11当前特点：**低误并优先，召回还可以继续扩**

最新汇总见 [round_07_all15_merge_v7_summary.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_summary.json:1)：

- 输入实体 mention：`13363`
- 唯一 entity form：`9761`
- candidate pairs：`524`
- 自动 merge：`453`
- uncertain：`69`
- blocked：`2`
- 合并后 cluster：`9354`
- 节点净减少：`407`

从 15 本书规模看，这版是偏保守的，不算“找尽了所有重复词语”，但已经把危险误并压得比较低。

## 核心原则

任务11当前遵循的是：

- 只合并“确定是同一个概念的不同表达”
- 不合并“只是看起来像”的词
- 采用 `召回 -> 评分筛选 -> 人工兜底`

也就是说，目标不是“所有相似词都并掉”，而是：

- 同一语义
- 同一抽象层级
- 非歧义表达

才允许自动 merge。

## 典型例子

可以自动合并：

- `机器学习` / `machine learning` / `Machine learning`
- `主成分分析` / `principal component analysis` / `PCA`
- `奇异值分解` / `singular value decomposition` / `SVD`
- `heat map` / `heatmap` / `heat maps`
- `p-value` / `P value` / `p-values`

不会自动合并：

- `ML`
- `machine learning` ↔ `machine learning ROM`
- `correlation` ↔ `correlation coefficient`
- `Controllability` ↔ `Controllability matrix`
- `Conversion` ↔ `conversion rate`

这里最重要的边界是：`ML` 是歧义缩写，不能全局默认等于 `machine learning`。

## 核心文件

- Merge 脚本：[run_entity_merge_harness.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_entity_merge_harness.py:1)
- Harness 说明：[task11_entity_merge_harness.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_entity_merge_harness.md:1)
- Seed alias：[entity_merge_seed_aliases.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/entity_merge_seed_aliases.json:1)
- 歧义缩写清单：[entity_merge_ambiguous_acronyms.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/entity_merge_ambiguous_acronyms.json:1)
- 最新 round 报告：[round_07_all15_merge_v7.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_rounds/round_07_all15_merge_v7.md:1)

## 关键输出

- 合并簇：[round_07_all15_merge_v7_clusters.jsonl](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_clusters.jsonl)
- 汇总：[round_07_all15_merge_v7_summary.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_summary.json)
- 表面变体板：[surface_variants](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_board_surface_variants.jsonl)
- 词形变体板：[inflection_variants](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_board_inflection_variants.jsonl)
- 显式别名板：[explicit_aliases](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_board_explicit_aliases.jsonl)
- 角色拦截板：[blocked_by_role](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_board_blocked_by_role.jsonl)
- 待继续扩召回的 backlog：[recall_backlog](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/entity_merge/round_07_all15_merge_v7_recall_backlog.jsonl)

## 怎么运行

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
python3 test_prompt/run_entity_merge_harness.py
```

只预览不写结果：

```bash
python3 test_prompt/run_entity_merge_harness.py --dry-run
```

## 下一个同学最该注意的边界

- 不要把任务11塞回 Prompt。
- 不要用“大词库硬并”替代审计式合并。
- 不要把 `ML`、`AI` 这类歧义缩写直接自动并掉。
- 如果目标是继续提高召回，优先看 `recall_backlog`，不要先放松 merge gate。

## 建议交接口径

可以对外这样描述：

> 任务11已完成一套独立于 Prompt 的实体合并 harness，当前基线为 `round_07_all15_merge_v7`。该版本以低误并为优先，已能稳定处理表面变体、单复数、显式别名和部分中英对照，但对更多跨书同义表达仍采用保守 review / backlog 策略，尚有继续扩召回空间。

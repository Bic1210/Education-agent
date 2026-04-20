# Task10 Round 01 - first10_trial

## 1. 本轮目标

- 启动前 10 本书的第一轮批量抽取
- 验证 `v4` prompt 在跨书场景下的稳定性
- 为后续抽样检查、问题记录、prompt 再迭代建立第一轮正式 batch 记录

## 2. 批量运行配置

- Prompt 版本：`v4`
- Batch name：`batch_v4_first10`
- 书目范围：前 10 本可用书目
- Chunk 范围：按当前语料库全部可用 chunk（最小字符数 250）
- 运行命令：

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
.venv/bin/python test_prompt/run_batch_extraction.py \
  --batch-name batch_v4_first10 \
  --prompt-version v4 \
  --max-books 10 \
  --sleep-seconds 1
```
- 结果文件：`test_prompt/results/batches/batch_extract_batch_v4_first10.jsonl`
- Summary 文件：`test_prompt/results/batches/batch_extract_batch_v4_first10_summary.json`
- Manifest 文件：`test_prompt/results/batches/batch_extract_batch_v4_first10_manifest.json`

## 3. 本轮检查计划

- 等 batch 正常落盘后，先抽样检查若干书与 chunk
- 将发现的问题记录到：
  [task10_issue_ledger.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_issue_ledger.md:1)
- 若发现结构性问题，再进入下一轮 prompt 修改

## 4. 当前状态

- `round_01` 已建立
- 批量抽取已完成
- 开始时间：`2026-04-18 22:11:30`
- 结束时间：`2026-04-19 04:53:41`
- 候选 chunk：`2008`
- 本轮处理：`2008`
- 成功：`1993`
- 失败：`15`
- 成功率：约 `99.25%`

## 5. 运行中早期观察

- 当前 batch：`batch_v4_first10`
- 已稳定完成并持续落盘
- 早期样本显示：
  - Book 01 chunk 4 出现重复实体名 `POD mode`，被校验拦截为错误
  - Book 01 的导言段落中出现一些教学价值偏低、定义偏泛的概念堆积
  - Book 01 chunk 3 抽取为空，需后续结合原文判断是否漏抽
- 全量跑完后新增观察：
  - `15` 条失败中，`8` 条是 JSON 格式损坏，说明 v4 在长段落上的结构化输出稳定性仍不够
  - `4` 条是实体字段缺失（`id/name/type`），说明“每个实体必须完整输出字段”的约束还会丢
  - `1` 条关系引用了不存在的实体 id，说明关系输出前的一致性检查不稳
  - 失败样本主要集中在英文书，尤其是长 chunk、术语密集段和方法综述段

## 6. 已记录到问题台账

- `T10-002` 重复实体名导致单条失败
- `T10-003` 导言段低价值泛化实体
- `T10-004` 空结果是否合理待判定
- `T10-005` 技术方法关系漂移（PCA / SVD 段）
- `T10-006` 空 definition 与弱 definition
- `T10-007` 长段 JSON 输出不稳
- `T10-008` 实体字段缺失
- `T10-009` 关系引用悬空 id

## 7. 本轮结论

- `v4` 已经具备大规模跑通能力，但还不能直接当作任务10终版
- 当前问题已经分成两类：
  - 质量类问题：低价值实体、空结果可疑、关系漂移、弱定义
  - 结构类问题：JSON 损坏、字段缺失、关系引用悬空
- 下一步不应直接扩大到全部书目，而应先做抽样复查并决定：
  - 哪些问题继续靠 prompt 收紧
  - 哪些问题需要加轻量后处理保护

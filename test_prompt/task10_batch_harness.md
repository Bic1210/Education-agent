# 任务10：批量抽取 Harness

任务10的目标是：在 prompt 已经迭代到当前可用版本后，批量处理多本书的所有文本段落，自动调用 API，产出结构化图谱数据。

这个 harness 仍然只放在 `test_prompt/` 下，不碰主流程目录。

## 这不是一次性脚本

任务10继续沿用 harness 思维：

- 批量跑
- 抽样看
- 记录问题
- 改 prompt
- 再跑

相关补充文档：

- [task10_harness_workflow.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_harness_workflow.md:1)
- [task10_issue_ledger.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_issue_ledger.md:1)
- [task10_rounds/round_00_batch_harness_setup.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_rounds/round_00_batch_harness_setup.md:1)

## 核心脚本

- [run_batch_extraction.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_batch_extraction.py:1)

## 设计原则

1. 可续跑
- 同一个 `batch-name` 重跑时，会自动跳过已经成功的 chunk
- 失败记录不会被跳过，后续可继续重试

2. 结果持续落盘
- 每个 chunk 处理完就写一条 JSONL
- summary 也会持续更新

3. 可先小批量、再全量
- 可限制书本数
- 可限制每本书 chunk 数
- 可限制总 chunk 数

4. 与任务9共用 Prompt 版本
- 当前支持 `v2 / v3 / v4`
- 默认使用当前完成版 `v4`

## 输出位置

全部仍然放在：

- `test_prompt/results/batches/`

每个 batch 会产出：

- `<prefix>_<batch-name>.jsonl`
- `<prefix>_<batch-name>_summary.json`
- `<prefix>_<batch-name>_manifest.json`

## 推荐工作流

### 1. 先做一轮小批量 smoke test

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
.venv/bin/python test_prompt/run_batch_extraction.py \
  --batch-name smoke_v4_2books \
  --prompt-version v4 \
  --book "04_Practical Statistics for Data Scientists" \
  --book "09_可解释人工智能导论" \
  --chunk-limit-per-book 5 \
  --sleep-seconds 1
```

### 2. 再做 10 本书试跑

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
.venv/bin/python test_prompt/run_batch_extraction.py \
  --batch-name batch_v4_first10 \
  --prompt-version v4 \
  --max-books 10 \
  --sleep-seconds 1
```

跑完后，不要直接宣布任务10完成，应继续：

1. 抽样若干书和 chunk
2. 记录问题到 `task10_issue_ledger.md`
3. 在 `task10_rounds/` 新建本轮记录
4. 如有必要再改 prompt，进入下一轮

### 3. 最后做当前全部可用书目

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
.venv/bin/python test_prompt/run_batch_extraction.py \
  --batch-name batch_v4_all_available \
  --prompt-version v4 \
  --sleep-seconds 1
```

## 续跑方式

如果某次中断，只要重复同一条命令、保持同一个 `--batch-name`：

```bash
.venv/bin/python test_prompt/run_batch_extraction.py \
  --batch-name batch_v4_first10 \
  --prompt-version v4 \
  --max-books 10 \
  --sleep-seconds 1
```

脚本会自动跳过已成功的 chunk，只继续处理剩余部分。

## Dry Run

先预览要处理多少书、多少 chunk：

```bash
.venv/bin/python test_prompt/run_batch_extraction.py \
  --batch-name preview_v4_all \
  --prompt-version v4 \
  --max-books 10 \
  --dry-run
```

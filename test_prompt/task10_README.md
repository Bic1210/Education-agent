# 任务10 README：15 本书批量抽取

任务10的目标是：在任务9已有可用 Prompt 基线的前提下，批量处理全部书籍 chunk，自动调用接口，产出结构化知识图谱抽取结果。

这份 README 是给下一个同学的最终交接口径。详细 harness 说明和逐轮记录继续保留在原文件中。

## 最终结论

- 任务10工程口径：**通过**
- 任务10质量口径：**条件通过**

当前最终统计来自 [batch_extract_batch_v4_all15_final_stats.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_all15_final_stats.json:1)：

- 覆盖书本：`15/15`
- 唯一 chunk：`2501/2501`
- `remaining_error_keys = 0`
- 当前最终抽取基线：`prompt_v4`

注意：工程上已经完整跑通，但 Prompt 抽样质量在任务9里仍未完全封板，所以不能把“全量跑完”误写成“抽取质量已最终达标”。

## 最终口径文件

- 任务10验收报告：[task10_acceptance_report.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/task10_acceptance_report.md:1)
- 最终统计：[batch_extract_batch_v4_all15_final_stats.json](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_all15_final_stats.json:1)
- 15 本合并去重结果：[batch_extract_batch_v4_all15_deduped.jsonl](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_all15_deduped.jsonl)
- 前 10 本去重结果：[batch_extract_batch_v4_first10_deduped.jsonl](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_first10_deduped.jsonl)
- 后 5 本去重结果：[batch_extract_batch_v4_remaining5_deduped.jsonl](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_remaining5_deduped.jsonl)

## 核心脚本与文档

- 批量抽取脚本：[run_batch_extraction.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_batch_extraction.py:1)
- Harness 说明：[task10_batch_harness.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_batch_harness.md:1)
- 工作流说明：[task10_harness_workflow.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_harness_workflow.md:1)
- 问题台账：[task10_issue_ledger.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_issue_ledger.md:1)
- round 记录目录：`test_prompt/task10_rounds/`

## 哪个批次才是最终基线

最终基线不是 `batch_v4_all_available`。

原因：

- `batch_v4_all_available` 是未完成的早期尝试，只处理到 `46/2501`
- 最终正确口径应使用：
  - `batch_v4_first10`
  - `batch_v4_remaining5`
  - 再按 `(book_file, chunk_index)` 去重合并

已经合并好的最终文件就是：

- [batch_extract_batch_v4_all15_deduped.jsonl](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_all15_deduped.jsonl)

## 这个任务已经完成了什么

- 跑通了可续跑的批量 harness
- 支持失败重试
- 支持 summary / manifest 持续落盘
- 已经把 15 本书全部抽完
- 已经清零残余失败
- 已经给出最终验收报告

## 这个任务没有解决什么

- 没有解决跨 chunk、跨书的实体合并
- 没有统一标准化 alias / canonical name
- 没有把“相似词”自动并成一个节点

这些都已经转到任务11处理。

## 如需重跑

只在需要补跑或换 Prompt 版本时重跑。默认不要重做全量。

示例：

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
.venv/bin/python test_prompt/run_batch_extraction.py \
  --batch-name batch_v4_first10 \
  --prompt-version v4 \
  --max-books 10 \
  --sleep-seconds 1
```

后续续跑会自动跳过已成功的 chunk，只重试失败项。

## 建议交接口径

可以对外这样描述：

> 任务10已完成 15 本书、2501 个唯一 chunk 的批量抽取与结果落盘，工程验收通过；最终交付口径以 `batch_extract_batch_v4_all15_deduped.jsonl` 和 `task10_acceptance_report.md` 为准。抽取质量仍受任务9 Prompt 上限约束，因此质量口径为条件通过。

# Task10 Round 00 - Batch Harness Setup

## 1. 本轮目标

- 在 `test_prompt/` 下建立任务10的批量抽取 harness
- 保持和任务9一致的“跑 -> 看 -> 记 -> 改 -> 再跑”流程

## 2. 已完成内容

- 新增批量抽取脚本：
  [run_batch_extraction.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_batch_extraction.py:1)
- 新增任务10说明：
  [task10_batch_harness.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_batch_harness.md:1)
- 新增本轮 workflow：
  [task10_harness_workflow.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_harness_workflow.md:1)
- 新增问题台账：
  [task10_issue_ledger.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_issue_ledger.md:1)
- 新增 round 模板：
  [templates/task10_round_record_template.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/templates/task10_round_record_template.md:1)
- 新增 prompt 修改记录模板：
  [templates/prompt_change_log_template.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/templates/prompt_change_log_template.md:1)

## 3. 已验证

- dry-run 可以正确预览前 10 本书和 chunk 数
- smoke batch `smoke_v4_2books_2chunks` 已成功跑通
- 同一 `batch-name` 重跑时会自动跳过已成功 chunk，续跑逻辑正常

## 4. 结论

- 任务10现在不是“只有批量脚本”，而是已经具备 harness 基础设施
- 后续每轮批量抽取都应在 `task10_rounds/` 下留记录
- 后续 prompt 调整也应同步记录到 change log 中


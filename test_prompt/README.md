# Test Prompt Workspace

这个目录专门用于任务7-任务9的 Prompt 设计、复跑和人工评估，不碰主流程代码。

现在任务10和任务11的批量抽取、实体合并产物也统一收在这个目录下。

## 交接入口

- 任务7：[task7_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task7_README.md:1)
- 任务9：[task9_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task9_README.md:1)
- 任务10：[task10_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task10_README.md:1)
- 任务11：[task11_README.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task11_README.md:1)

## 当前文件

- `task7_test.py`
  任务7同学留下的单条测试脚本
- `task7_README.md`
  任务7设计说明
- `task8.md`
  任务8工作汇报
- `评估总结.md`
  任务8评估结论摘要
- `eval_report_08 (1).csv`
  任务8原始评估表
- `eval_report_08_scored.csv`
  任务8已评分评估表
- `prompt_v2.py`
  基于任务8评估结果收紧后的 Prompt v2
- `run_prompt_eval_v2.py`
  用于小批量复跑 Prompt v2 的脚本
- `review_prompt_v1.py`
  “第二个助手”的评审 Prompt
- `run_review_assistant.py`
  批量复审抽取结果、输出驳回意见的脚本
- `task9_prompt_iteration.md`
  v2 的修改说明
- `task9_execution_template.md`
  任务9的执行模板
- `task9_README.md`
  任务9交接说明
- `review_assistant_README.md`
  评审助手使用说明
- `run_batch_extraction.py`
  任务10的批量抽取 harness
- `task10_batch_harness.md`
  任务10运行说明
- `task10_harness_workflow.md`
  任务10的 harness 迭代流程
- `task10_issue_ledger.md`
  任务10批量问题台账
- `task10_README.md`
  任务10交接说明
- `run_entity_merge_harness.py`
  任务11实体合并 harness
- `task11_entity_merge_harness.md`
  任务11运行说明
- `task11_README.md`
  任务11交接说明

## 建议目录用途

- `templates/`
  固定模板，复制后填写
- `rounds/`
  每一轮 prompt 迭代的记录
- `results/`
  脚本跑出来的 JSONL / summary 结果

## 推荐工作流

1. 先看 `评估总结.md` 和 `eval_report_08_scored.csv`
2. 在 `prompt_v2.py` 或后续版本里修改 Prompt
3. 用 `run_prompt_eval_v2.py` 复跑固定样本
4. 把本轮结论记录到 `rounds/`
5. 人工评估后决定是否进入下一轮

## 先跑固定样本

建议先固定 Book 04 和 Book 09 的同一批 chunk，用来做版本对比：

- Book 04: `chunk_index = 5,6,7,8`
- Book 09: `chunk_index = 5,6,7,8`

先预览会跑哪些数据：

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
python3 test_prompt/run_prompt_eval_v2.py --dry-run --chunk-indexes 5,6,7,8 --max-chunks 4
```

正式跑：

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
export OPENAI_API_KEY="your-key"
python3 test_prompt/run_prompt_eval_v2.py --chunk-indexes 5,6,7,8 --max-chunks 4
```

## 达标判断

任务9不是“把 prompt 改得更长”，而是要看复跑后是否真实提升：

- 冗余实体是否减少
- 评测维度误抽是否减少
- `包含` 方向是否更稳定
- 定义是否更具体
- 关系是否更少但更准

如果这些没有明显改善，就继续下一轮，而不是直接进入任务10。

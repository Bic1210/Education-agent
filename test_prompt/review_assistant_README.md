# Review Assistant

这个“第二个助手”用于在每一轮抽取结束后，自动对结果做一轮严格复审，模拟人工审核。

## 它做什么

- 读取上一轮抽取结果 JSONL
- 将原文段落和抽取结果一起送给评审模型
- 给出 `accept / revise / reject`
- 输出问题类别、具体理由、下一轮 prompt 修改重点
- 自动生成一份 round 报告，写入 `test_prompt/rounds/`

## 相关文件

- `review_prompt_v1.py`
  评审助手使用的 Prompt
- `run_review_assistant.py`
  批量复审脚本

## 运行方式

先完成一轮抽取，例如已有：

- `test_prompt/results/prompt_v2_eval_20260418_204626.jsonl`

然后运行：

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
.venv/bin/python test_prompt/run_review_assistant.py \
  --results-file test_prompt/results/prompt_v2_eval_20260418_204626.jsonl \
  --round-name round_01_v2_review
```

## 输出

- `test_prompt/results/<round-name>_review_v1.jsonl`
- `test_prompt/results/<round-name>_review_v1_summary.json`
- `test_prompt/rounds/<round-name>.md`

## 推荐工作流

1. 跑一轮抽取
2. 立刻跑一轮评审助手
3. 看 `rounds/*.md` 中的驳回理由
4. 只针对高频问题修改 prompt
5. 进入下一轮


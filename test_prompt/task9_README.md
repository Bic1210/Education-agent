# 任务9 README：Prompt 迭代与评估

任务9的目标是：基于任务8的人工评估结果，持续迭代抽取 Prompt，并用固定样本复跑验证质量是否改善。

这份 README 不是逐轮日志，而是给下一个同学的接手说明。详细 round 记录仍然保留在 `rounds/` 下。

## 当前结论

- 已完成 `v2 -> v3 -> v4` 三轮 Prompt 迭代。
- 当前默认可用版本是 [prompt_v4.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_v4.py:1)。
- 任务10 和任务11 的批量结果都基于 `v4`。
- 但任务9 **还不能算“质量已经封板”**。

原因很直接，三轮复审都没有出现“稳定 accept”：

- [round_01_v2_review.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/rounds/round_01_v2_review.md:1): `accept 0 / revise 6 / reject 2`
- [round_02_v3_review.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/rounds/round_02_v3_review.md:1): `accept 0 / revise 8 / reject 0`
- [round_03_v4_review.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/rounds/round_03_v4_review.md:1): `accept 0 / revise 7 / reject 1`

所以当前口径应写成：

- 任务9：**已完成迭代流程与可用版本沉淀**
- 任务9：**未完成质量封板**

## 核心输入

- 任务8评估汇总：[评估总结.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/评估总结.md:1)
- 任务8工作记录：[task8.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task8.md:1)
- 已评分表格：`test_prompt/eval_report_08_scored.csv`

任务8里最关键的问题有：

- 跨 chunk 重复提取
- 定义空洞或定义有误
- 冗余/过于工具化的实体
- 关系类型错误或方向错误
- 评测维度误作节点

其中“跨 chunk / 跨书重复”不再由 Prompt 解决，后续已经转交任务11。

## 核心文件

- Prompt 注册表：[prompt_registry.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_registry.py:1)
- Prompt v2：[prompt_v2.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_v2.py:1)
- Prompt v3：[prompt_v3.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_v3.py:1)
- Prompt v4：[prompt_v4.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_v4.py:1)
- 小批量复跑脚本：[run_prompt_eval_v2.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_prompt_eval_v2.py:1)
- 评审 Prompt：[review_prompt_v1.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/review_prompt_v1.py:1)
- 评审脚本：[run_review_assistant.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_review_assistant.py:1)
- 任务9说明：[task9_prompt_iteration.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task9_prompt_iteration.md:1)
- 任务9执行模板：[task9_execution_template.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/task9_execution_template.md:1)

## 当前推荐基线

如果只是为了继续全链路工作，不需要再回退到 `v2` 或 `v3`，直接以 `v4` 为当前基线：

- 抽取基线：`prompt_v4`
- 评审基线：`review_v1`
- 对比样本：Book 04 + Book 09 的固定 chunk

## 怎么复跑

先做小样本复跑：

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
export OPENAI_API_KEY="your-key"
python3 test_prompt/run_prompt_eval_v2.py \
  --prompt-version v4 \
  --chunk-indexes 5,6,7,8 \
  --max-chunks 4
```

再对输出做复审：

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent
export OPENAI_API_KEY="your-key"
python3 test_prompt/run_review_assistant.py \
  --input-jsonl test_prompt/results/<your_output>.jsonl
```

## 下一个同学最该注意的边界

- 不要再试图用 Prompt 解决全局实体去重。
- 不要把“多抽一点”误当成“质量更好”。
- 若继续迭代，必须固定样本，不要换一批 chunk 再比较。
- 若问题是跨 chunk / 跨书别名归一，直接看任务11，不要继续往 Prompt 里硬塞规则。

## 建议交接口径

可以对外这样描述：

> 任务9已完成三轮 Prompt 迭代，并沉淀出可用于任务10批量抽取的 `v4` 基线；但从抽样复审结果看，Prompt 质量仍有 revise/reject，故该任务在“流程完成”层面已达成，在“质量封板”层面仍未完全达标。

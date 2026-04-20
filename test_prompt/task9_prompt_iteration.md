# 任务9：Prompt 迭代说明

本轮迭代基于 [评估总结.md](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/评估总结.md:1) 和 `eval_report_08_scored.csv` 的问题归纳，目标不是增加抽取数量，而是降低“过度概括、过度解读、关系冗余”。

## v2 重点修改

1. 收紧实体准入条件
- 明确要求“拿不准就不提取”
- 禁止把评测指标、评价维度、性质、子属性单独抽成实体
- 禁止提取只在局部举例中出现、过于具体、过于工具化的词

2. 收紧关系输出条件
- 只允许输出有直接文本依据的关系
- 明确“关系要少而精”，避免同段内实体全连接
- 如果方向无法确定，直接不输出

3. 强化 `包含` 的方向约束
- 新增硬规则：`A 是一种 B` 等价于 `source=B, target=A`
- 要求模型输出前自检 `包含` 方向

4. 修正类型边界
- 可视化图表、统计图形、列联表优先归为 `concept`
- 软件、框架、库、平台才归为 `tool`
- 方法、模型、检验、估计方法优先归为 `algorithm`

5. 修正定义质量
- definition 必须写核心区分特征
- 禁止“与XX相关的概念”“一种方法”这类空泛定义
- 若原文定义信息不足，允许返回空字符串，避免硬编

## 和任务8评估结论的对应关系

| 任务8问题 | v2处理方式 |
|---|---|
| 定义空洞或定义有误 | 强化 definition 规则，信息不足时允许空字符串 |
| 冗余/过于工具化的实体 | 收紧实体准入条件，拿不准不提取 |
| 实体类型标注错误 | 增加 `concept` / `algorithm` / `tool` 反例说明 |
| 关系类型错误 | 收紧关系触发条件，减少弱关系 |
| 关系方向错误 | 明确 `包含` 的方向映射与自检要求 |
| 评测维度误作节点 | 显式禁止提取评测指标/性质/子属性 |
| 跨 chunk 重复 | 不在 prompt 内解决，后续交给任务11合并去重 |

## 本轮产物

- [prompt_v2.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/prompt_v2.py:1)
- [run_prompt_eval_v2.py](/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/run_prompt_eval_v2.py:1)

## 建议的复跑方式

先只复跑 Book 04 和 Book 09 的少量 chunk，对比 v1 与 v2 的实体数、关系数和人工问题率。

示例：

```bash
cd /mnt/d/ayibike/video/education/second/EducationAgent/test_prompt
export OPENAI_API_KEY="your-key"
python3 run_prompt_eval_v2.py --chunk-indexes 5,6,7,8 --max-chunks 4
```

运行结果会写入 `test_prompt/results/`，不会污染主项目目录。


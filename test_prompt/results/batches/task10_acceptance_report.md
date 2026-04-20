# Task10 Acceptance Report

## Final Verdict
- 工程口径：通过
- 质量口径：条件通过
- 说明：任务10要求的“15本书批量抽取跑通并产出结构化结果”已完成；但 prompt 质量在任务9的抽样评审里仍有改进空间。

## Acceptance Checks
- 15 本覆盖：`15/15`
- candidate chunks 覆盖：`2501/2501`
- remaining_error_keys：`0`
- first10 最终补跑：`15/15` 成功，结束于 `20260420_021736`
- remaining5 最终补跑：残余错误 `0`，结束于 `20260420_005534`

## Why This Is The Final Baseline
- `batch_v4_all_available` 只处理到 46/2501，是未完成批次，不能作为最终口径。
- 最终口径应使用 `batch_v4_first10` 与 `batch_v4_remaining5` 的去重结果合并。

## Per Book
- `01_Data-Driven Science and Engineering Machine Learning, Dynamical Systems, and Control (Steven L. Brunton, J. Nathan Kutz) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=222/222 | success=222 | error=0 | entities=1295 | relations=508
- `02_Foundations of Data Science (Avrim Blum, John Hopcroft, Ravindran Kannan) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=210/210 | success=210 | error=0 | entities=1026 | relations=323
- `03_Game Analytics Maximizing the Value of Player Data (Magy Seif El-Nasr, Anders Drachen etc.) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=538/538 | success=538 | error=0 | entities=2697 | relations=876
- `04_Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=140/140 | success=140 | error=0 | entities=851 | relations=263
- `05_Quantifying the User Experience Practical Statistics For User Research (Jeff Sauro, James R Lewis) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=189/189 | success=189 | error=0 | entities=937 | relations=313
- `06_Storytelling with Data (Cole Nussbaumer Knaflic) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=98/98 | success=98 | error=0 | entities=362 | relations=99
- `07_The truthful art  data, charts, and maps for communication (Cairo, Alberto, 1974- author) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=70/70 | success=70 | error=0 | entities=331 | relations=105
- `08_Usability and User Experience Design The Comprehensive Guide to Data-Driven UX Design (Benjamin Franz, Michaela Kauer-Franz) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=435/435 | success=435 | error=0 | entities=1825 | relations=509
- `09_可解释人工智能导论 (杨强 等) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=58/58 | success=58 | error=0 | entities=421 | relations=149
- `10_大数据与人工智能导论 (姚海鹏, 王露瑶, 刘韵洁) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=48/48 | success=48 | error=0 | entities=415 | relations=207
- `11_数据科学的概率基础 (王学钦，赵鹏主编, 王学钦,赵鹏主编, 王学钦, 赵鹏) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=36/36 | success=36 | error=0 | entities=217 | relations=95
- `12_资深游戏设计师25年实践经验结晶，通过量实例深入讲解了角色扮演游戏、实时战略游.json` | unique=161/161 | success=161 | error=0 | entities=601 | relations=165
- `13_游戏设计师修炼之道 数据驱动的游戏设计 (Pdg2Pic, （美）摩尔著) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=203/203 | success=203 | error=0 | entities=1478 | relations=677
- `14_知识图谱：方法、实践与应用 (王昊奋  漆桂林  陈华钧 主编) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=92/92 | success=92 | error=0 | entities=892 | relations=464
- `15_数据驱动设计：AB测试提升用户体验 (【美】罗谢尔·肯（Rochelle King）等) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=1/1 | success=1 | error=0 | entities=15 | relations=0

## Artifacts
- first10_deduped: `test_prompt/results/batches/batch_extract_batch_v4_first10_deduped.jsonl`
- combined_all15_deduped: `test_prompt/results/batches/batch_extract_batch_v4_all15_deduped.jsonl`
- combined_stats: `test_prompt/results/batches/batch_extract_batch_v4_all15_final_stats.json`

## Metadata Warnings
- 若后续要做统计或展示，请以 `book_file` 为准，`book_title` 在部分书上有串位。
- `12_资深游戏设计师25年实践经验结晶，通过量实例深入讲解了角色扮演游戏、实时战略游.json` | expected≈`资深游戏设计师25年实践经验结晶，通过量实例深入讲解了角色扮演游戏、实时战略游` | observed=`游戏设计师修炼之道 数据驱动的游戏设计 (Pdg2Pic, （美）摩尔著)`
- `13_游戏设计师修炼之道 数据驱动的游戏设计 (Pdg2Pic, （美）摩尔著) (z-library.sk, 1lib.sk, z-lib.sk).json` | expected≈`游戏设计师修炼之道 数据驱动的游戏设计 (Pdg2Pic, （美）摩尔著) (z-library.sk, 1lib.sk, z-lib.sk)` | observed=`知识图谱：方法、实践与应用 (王昊奋  漆桂林  陈华钧 主编)`
- `14_知识图谱：方法、实践与应用 (王昊奋  漆桂林  陈华钧 主编) (z-library.sk, 1lib.sk, z-lib.sk).json` | expected≈`知识图谱：方法、实践与应用 (王昊奋  漆桂林  陈华钧 主编) (z-library.sk, 1lib.sk, z-lib.sk)` | observed=`统计学习方法（第2版） (李航)`

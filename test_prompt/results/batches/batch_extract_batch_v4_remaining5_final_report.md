# batch_v4_remaining5 Final Report

## Overall
- batch: `batch_v4_remaining5`
- prompt_version: `v4`
- model: `deepseek-reasoner`
- raw_rows: `499`
- unique_chunk_keys: `493`
- superseded_rows: `6`
- remaining_error_keys: `0`
- final_started_at: `20260419_133809`
- final_finished_at: `20260420_005455`

## Per Book
- `11_数据科学的概率基础 (王学钦，赵鹏主编, 王学钦,赵鹏主编, 王学钦, 赵鹏) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=36/36 | success=36 | error=0 | entities=217 | relations=95
- `12_资深游戏设计师25年实践经验结晶，通过量实例深入讲解了角色扮演游戏、实时战略游.json` | unique=161/161 | success=161 | error=0 | entities=601 | relations=165
- `13_游戏设计师修炼之道 数据驱动的游戏设计 (Pdg2Pic, （美）摩尔著) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=203/203 | success=203 | error=0 | entities=1478 | relations=677
- `14_知识图谱：方法、实践与应用 (王昊奋  漆桂林  陈华钧 主编) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=92/92 | success=92 | error=0 | entities=892 | relations=464
- `15_数据驱动设计：AB测试提升用户体验 (【美】罗谢尔·肯（Rochelle King）等) (z-library.sk, 1lib.sk, z-lib.sk).json` | unique=1/1 | success=1 | error=0 | entities=15 | relations=0

## Files
- deduped_jsonl: `test_prompt/results/batches/batch_extract_batch_v4_remaining5_deduped.jsonl`
- final_stats_json: `test_prompt/results/batches/batch_extract_batch_v4_remaining5_final_stats.json`
- source_summary_json: `test_prompt/results/batches/batch_extract_batch_v4_remaining5_summary.json`

## Metadata Warnings
- `book_title` metadata is inconsistent for some books; stats above use `book_file` as the source of truth.
- `12_资深游戏设计师25年实践经验结晶，通过量实例深入讲解了角色扮演游戏、实时战略游.json` | expected≈`资深游戏设计师25年实践经验结晶，通过量实例深入讲解了角色扮演游戏、实时战略游` | observed=`游戏设计师修炼之道 数据驱动的游戏设计 (Pdg2Pic, （美）摩尔著)`
- `13_游戏设计师修炼之道 数据驱动的游戏设计 (Pdg2Pic, （美）摩尔著) (z-library.sk, 1lib.sk, z-lib.sk).json` | expected≈`游戏设计师修炼之道 数据驱动的游戏设计 (Pdg2Pic, （美）摩尔著) (z-library.sk, 1lib.sk, z-lib.sk)` | observed=`知识图谱：方法、实践与应用 (王昊奋  漆桂林  陈华钧 主编)`
- `14_知识图谱：方法、实践与应用 (王昊奋  漆桂林  陈华钧 主编) (z-library.sk, 1lib.sk, z-lib.sk).json` | expected≈`知识图谱：方法、实践与应用 (王昊奋  漆桂林  陈华钧 主编) (z-library.sk, 1lib.sk, z-lib.sk)` | observed=`统计学习方法（第2版） (李航)`

# round_03_all15_merge_v3

## 总结

- 输入文件：`/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_all15_deduped.jsonl`
- 原始实体 mention：`13363`
- 唯一实体 form：`9761`
- 自动 merge 决策：`521`
- uncertain 候选：`379`
- 合并后 cluster：`9307`
- 节点净减少：`454`

## 设计口径

- 本轮只自动合并高置信等价项：表面规范化变体、seed alias、括号别名、明确 acronym-longform。
- 共享词根、上下位、方法家族词只打到 uncertain，不自动并。

## 板块统计

- surface_variants：`297`
- inflection_variants：`191`
- explicit_aliases：`33`
- ambiguous_acronyms：`0`
- risky_review：`379`

## 高风险待审样本

- `correlation` ↔ `correlation coefficient` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `correlation` ↔ `correlation matrix` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `confidence interval` ↔ `confidence` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `sample size` ↔ `sample size per iteration` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `sample size` ↔ `sample size requirements` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `clustering` ↔ `clustering problem` | type=`task` | reason=`surface_containment` | confidence=`0.55`
- `Boosting` ↔ `Boosting Algorithm` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `confidence` ↔ `confidence intervals` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `confidence` ↔ `confidence level` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `hypothesis` ↔ `hypothesis class` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `covariance` ↔ `covariance matrix` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `hypothesis` ↔ `hypothesis test` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `hypothesis` ↔ `hypothesis testing` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `significance level` ↔ `significance level (α)` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `usability problem` ↔ `usability` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `machine learning` ↔ `machine learning ROM` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `visualization` ↔ `visualization techniques` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `Controllability` ↔ `controllability Gramian` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `Controllability` ↔ `Controllability matrix` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `Controllability` ↔ `Controllability Matrix` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `qualitative data` ↔ `qualitative data analysis` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `知识图谱表示学习` ↔ `知识图谱表示学习技术` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `chi-square test` ↔ `chi-square test of independence` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `clustering` ↔ `clustering algorithm` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `confidence` ↔ `Confidence Intervals` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `frequency` ↔ `frequency table` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `interaction` ↔ `interaction effect` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `interaction` ↔ `interaction principle` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `interaction` ↔ `interaction principles` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `population` ↔ `population mean` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `population` ↔ `population parameters` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `questionnaire` ↔ `questionnaire design` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `questionnaire` ↔ `Questionnaire design` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `statistical significance` ↔ `statistical significance of r` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `马尔可夫链蒙特卡洛` ↔ `马尔可夫链蒙特卡洛方法` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `contrast` ↔ `contrast coding` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `contrast` ↔ `contrast color` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `Efficiency` ↔ `efficiency scale` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `Efficiency` ↔ `efficiency term` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `feedback loop` ↔ `feedback` | type=`process` | reason=`surface_containment` | confidence=`0.55`
- `frequency` ↔ `frequency charts` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `frequency` ↔ `frequency distribution` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `frequency` ↔ `frequency moments` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `frequency` ↔ `frequency response` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `frequency` ↔ `Frequency table` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `k-means聚类` ↔ `k-means聚类算法` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `probability` ↔ `probability density` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `probability` ↔ `probability sampling` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `regression analysis` ↔ `regression` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `singular value` ↔ `Singular Value Decomposition` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `stakeholder` ↔ `stakeholder requirements` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `treatment` ↔ `treatment group` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `uncertainty principle` ↔ `uncertainty` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `usability problem` ↔ `Usability` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `user testing` ↔ `user test` | type=`task` | reason=`surface_containment` | confidence=`0.55`
- `usability` ↔ `usability engineering` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `usability` ↔ `usability feedback` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `usability` ↔ `usability metrics` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `usability` ↔ `usability problems` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `usability` ↔ `Usability requirements` | type=`concept` | reason=`surface_containment` | confidence=`0.55`

## 重点合并簇

- `principal component analysis` | members=`5` | mentions=`27` | books=`7` | 主成分分析, principal component analysis, principal components analysis, PCA, Principal Component Analysis
- `heat map` | members=`5` | mentions=`13` | books=`5` | heat map, heat maps, heatmap, heatmaps, Heatmaps
- `singular value decomposition` | members=`4` | mentions=`50` | books=`4` | 奇异值分解, singular value decomposition, SVD, Singular Value Decomposition
- `p-value` | members=`4` | mentions=`20` | books=`4` | p-value, p-values, P value, P-value
- `Proper Orthogonal Decomposition` | members=`4` | mentions=`11` | books=`1` | proper orthogonal decomposition, POD, Proper Orthogonal Decomposition, Proper Orthogonal Decomposition (POD)
- `norm` | members=`4` | mentions=`6` | books=`5` | norm, Norm, norms, Norms
- `Empathy maps` | members=`4` | mentions=`5` | books=`1` | Empathy maps, empathy map, empathy maps, Empathy Maps
- `map` | members=`4` | mentions=`5` | books=`3` | map, MAP, Map, maps
- `Neural Networks` | members=`4` | mentions=`5` | books=`1` | Neural Networks, neural network, Neural Network, neural networks
- `confidence interval` | members=`3` | mentions=`20` | books=`4` | confidence interval, confidence intervals, Confidence Intervals
- `context of use analysis` | members=`3` | mentions=`20` | books=`1` | context of use analysis, Context of Use Analysis, Context of use analysis
- `game metrics` | members=`3` | mentions=`20` | books=`1` | game metrics, game metric, Game Metrics
- `metrics` | members=`3` | mentions=`16` | books=`2` | metrics, metric, Metrics
- `game analytics` | members=`3` | mentions=`14` | books=`1` | game analytics, Game Analytics, Game analytics
- `machine learning` | members=`3` | mentions=`12` | books=`5` | 机器学习, machine learning, Machine learning
- `persona` | members=`3` | mentions=`12` | books=`2` | persona, personas, Personas
- `System Usability Scale` | members=`3` | mentions=`12` | books=`2` | SUS, System Usability Scale, System Usability Scale (SUS)
- `questionnaire` | members=`3` | mentions=`11` | books=`2` | questionnaire, questionnaires, Questionnaires
- `data-driven UX design` | members=`3` | mentions=`10` | books=`1` | data-driven UX design, Data-driven UX design, data-driven UX design (3DUX)
- `histogram` | members=`3` | mentions=`10` | books=`3` | histogram, Histogram, histograms

# round_01_all15_merge_v1

## 总结

- 输入文件：`/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_all15_deduped.jsonl`
- 原始实体 mention：`13363`
- 唯一实体 form：`9761`
- 自动 merge 决策：`330`
- uncertain 候选：`480`
- 合并后 cluster：`9458`
- 节点净减少：`303`

## 设计口径

- 本轮只自动合并高置信等价项：表面规范化变体、seed alias、括号别名、明确 acronym-longform。
- 共享词根、上下位、方法家族词只打到 uncertain，不自动并。

## 高风险待审样本

- `correlation` ↔ `correlation coefficient` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `correlation` ↔ `correlation matrix` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `confidence interval` ↔ `confidence` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `confidence interval` ↔ `confidence intervals` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `sample size` ↔ `sample size per iteration` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `sample size` ↔ `sample size requirements` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `sample mean` ↔ `sample means` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `confidence interval` ↔ `Confidence Intervals` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `data visualization` ↔ `data visualizations` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `clustering` ↔ `clustering problem` | type=`task` | reason=`surface_containment` | confidence=`0.55`
- `indicator variable` ↔ `indicator variables` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `Boosting` ↔ `Boosting Algorithm` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `confidence` ↔ `confidence intervals` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `confidence` ↔ `confidence level` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `hypothesis` ↔ `hypothesis class` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `independent variable` ↔ `independent variables` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
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
- `Net Promoter Score` ↔ `Net Promoter Scores` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `qualitative data` ↔ `qualitative data analysis` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `知识图谱表示学习` ↔ `知识图谱表示学习技术` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `chi-square test` ↔ `chi-square test of independence` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `clustering` ↔ `clustering algorithm` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `confidence` ↔ `Confidence Intervals` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `distance metric` ↔ `distance metrics` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
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
- `random projections` ↔ `Random Projection` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `regression analysis` ↔ `regression` | type=`algorithm` | reason=`surface_containment` | confidence=`0.55`
- `singular value` ↔ `Singular Value Decomposition` | type=`concept` | reason=`surface_containment` | confidence=`0.55`
- `singular value` ↔ `singular values` | type=`concept` | reason=`surface_containment` | confidence=`0.55`

## 重点合并簇

- `singular value decomposition` | members=`4` | mentions=`50` | books=`4` | 奇异值分解, singular value decomposition, SVD, Singular Value Decomposition
- `principal component analysis` | members=`4` | mentions=`24` | books=`6` | 主成分分析, principal component analysis, PCA, Principal Component Analysis
- `Proper Orthogonal Decomposition` | members=`4` | mentions=`11` | books=`1` | proper orthogonal decomposition, POD, Proper Orthogonal Decomposition, Proper Orthogonal Decomposition (POD)
- `context of use analysis` | members=`3` | mentions=`20` | books=`1` | context of use analysis, Context of Use Analysis, Context of use analysis
- `p-value` | members=`3` | mentions=`18` | books=`4` | p-value, P value, P-value
- `game analytics` | members=`3` | mentions=`14` | books=`1` | game analytics, Game Analytics, Game analytics
- `machine learning` | members=`3` | mentions=`12` | books=`5` | 机器学习, machine learning, Machine learning
- `System Usability Scale` | members=`3` | mentions=`12` | books=`2` | SUS, System Usability Scale, System Usability Scale (SUS)
- `data-driven UX design` | members=`3` | mentions=`10` | books=`1` | data-driven UX design, Data-driven UX design, data-driven UX design (3DUX)
- `Koopman operator` | members=`3` | mentions=`10` | books=`1` | Koopman operator, Koopman operator (continuous time), Koopman operator (discrete time)
- `overfitting` | members=`3` | mentions=`8` | books=`4` | overfitting, Overfitting, over-fitting
- `Dynamic Mode Decomposition` | members=`3` | mentions=`7` | books=`1` | Dynamic Mode Decomposition, dynamic mode decomposition, Dynamic mode decomposition
- `heat maps` | members=`3` | mentions=`6` | books=`3` | heat maps, heatmaps, Heatmaps
- `nonnegative matrix factorization` | members=`3` | mentions=`6` | books=`2` | nonnegative matrix factorization, Nonnegative Matrix Factorization, non-negative matrix factorization
- `ROI` | members=`3` | mentions=`6` | books=`2` | ROI, 投资回报率, ROI (投资回报率)
- `Backpropagation` | members=`3` | mentions=`5` | books=`2` | Backpropagation, back propagation, backpropagation
- `fast Fourier transform` | members=`3` | mentions=`5` | books=`1` | fast Fourier transform, Fast Fourier Transform, Fast Fourier transform
- `G(n, p) model` | members=`3` | mentions=`5` | books=`1` | G(n, p) model, G(n,p) model, GNP model
- `MapReduce` | members=`3` | mentions=`5` | books=`2` | Map Reduce, MapReduce, Map/Reduce
- `supervised learning` | members=`3` | mentions=`5` | books=`2` | supervised learning, Supervised Learning, Supervised learning

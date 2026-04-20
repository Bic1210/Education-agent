# round_07_all15_merge_v7

## 总结

- 输入文件：`/mnt/d/ayibike/video/education/second/EducationAgent/test_prompt/results/batches/batch_extract_batch_v4_all15_deduped.jsonl`
- 原始实体 mention：`13363`
- 唯一实体 form：`9761`
- 自动 merge 决策：`453`
- uncertain 候选：`69`
- 合并后 cluster：`9354`
- 节点净减少：`407`

## 设计口径

- 本轮只自动合并高置信等价项：表面规范化变体、seed alias、括号别名、明确 acronym-longform。
- 共享词根、头词、定义相近项先进入召回层，再由 score + gate 决定 merge / review / block。

## 板块统计

- surface_variants：`293`
- inflection_variants：`190`
- explicit_aliases：`36`
- ambiguous_acronyms：`0`
- blocked_by_role：`2`
- recall_review：`3`
- risky_review：`0`

## 高风险待审样本

- `outliers` ↔ `outlier` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `histogram` ↔ `histograms` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `questionnaire` ↔ `questionnaires` | type=`tool` | reason=`scored_review` | confidence=`0.82`
- `norm` ↔ `norms` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `norm` ↔ `Norms` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `metrics` ↔ `metric` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `persona` ↔ `personas` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `persona` ↔ `Personas` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `benchmark` ↔ `benchmarks` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `stakeholder` ↔ `stakeholders` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `variables` ↔ `variable` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `heatmap` ↔ `heatmaps` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `interaction` ↔ `interactions` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `questionnaire` ↔ `questionnaires` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `scale` ↔ `scales` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `graphs` ↔ `Graph` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `heatmap` ↔ `Heatmaps` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `stakeholder` ↔ `Stakeholders` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `RDF` ↔ `RDFS` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `prototype` ↔ `prototypes` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `requirements` ↔ `requirement` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `requirements` ↔ `Requirement` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `wireframe` ↔ `wireframes` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `assumption` ↔ `assumptions` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `N-1 chi-square test` ↔ `N-1 chi-squared test` | type=`algorithm` | reason=`scored_review` | confidence=`0.52`
- `user` ↔ `users` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `color` ↔ `colors` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `infographic` ↔ `infographics` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `workflow` ↔ `workflows` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `assumptions` ↔ `Assumption` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `goals` ↔ `goal` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `hyperparameters` ↔ `hyperparameter` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `users` ↔ `User` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `wireframes` ↔ `Wireframe` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `eigenfaces` ↔ `eigenface` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `icon` ↔ `Icons` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `map` ↔ `maps` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `metric` ↔ `Metrics` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `MMOG` ↔ `MMOGs` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `Prototype` ↔ `prototypes` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `resources` ↔ `resource` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `statistics` ↔ `statistic` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `wavelets` ↔ `wavelet` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `wavelets` ↔ `Wavelet` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `workflows` ↔ `Workflow` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `Boxplot` ↔ `boxplots` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `cone` ↔ `cones` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `cost` ↔ `Costs` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `disturbance` ↔ `disturbances` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `graphic` ↔ `Graphics` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `Histogram` ↔ `histograms` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `hyperparameter` ↔ `Hyperparameters` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `interval` ↔ `Intervals` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `Likert-type agreement item` ↔ `Likert-type item` | type=`concept` | reason=`scored_review` | confidence=`0.52`
- `MAP` ↔ `maps` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `Map` ↔ `maps` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `Measurement` ↔ `measurements` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `Norm` ↔ `norms` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `Norm` ↔ `Norms` | type=`concept` | reason=`scored_review` | confidence=`0.82`
- `path` ↔ `Paths` | type=`concept` | reason=`scored_review` | confidence=`0.82`

## 重点合并簇

- `principal component analysis` | members=`5` | mentions=`27` | books=`7` | 主成分分析, principal component analysis, principal components analysis, PCA, Principal Component Analysis
- `heat map` | members=`5` | mentions=`13` | books=`5` | heat map, heat maps, heatmap, heatmaps, Heatmaps
- `singular value decomposition` | members=`4` | mentions=`50` | books=`4` | 奇异值分解, singular value decomposition, SVD, Singular Value Decomposition
- `p-value` | members=`4` | mentions=`20` | books=`4` | p-value, p-values, P value, P-value
- `Proper Orthogonal Decomposition` | members=`4` | mentions=`11` | books=`1` | proper orthogonal decomposition, POD, Proper Orthogonal Decomposition, Proper Orthogonal Decomposition (POD)
- `Empathy maps` | members=`4` | mentions=`5` | books=`1` | Empathy maps, empathy map, empathy maps, Empathy Maps
- `Neural Networks` | members=`4` | mentions=`5` | books=`1` | Neural Networks, neural network, Neural Network, neural networks
- `confidence interval` | members=`3` | mentions=`20` | books=`4` | confidence interval, confidence intervals, Confidence Intervals
- `context of use analysis` | members=`3` | mentions=`20` | books=`1` | context of use analysis, Context of Use Analysis, Context of use analysis
- `game metrics` | members=`3` | mentions=`20` | books=`1` | game metrics, game metric, Game Metrics
- `game analytics` | members=`3` | mentions=`14` | books=`1` | game analytics, Game Analytics, Game analytics
- `machine learning` | members=`3` | mentions=`12` | books=`5` | 机器学习, machine learning, Machine learning
- `System Usability Scale` | members=`3` | mentions=`12` | books=`2` | SUS, System Usability Scale, System Usability Scale (SUS)
- `questionnaire` | members=`3` | mentions=`11` | books=`2` | questionnaire, questionnaires, Questionnaires
- `data-driven UX design` | members=`3` | mentions=`10` | books=`1` | data-driven UX design, Data-driven UX design, data-driven UX design (3DUX)
- `Koopman operator` | members=`3` | mentions=`10` | books=`1` | Koopman operator, Koopman operator (continuous time), Koopman operator (discrete time)
- `overfitting` | members=`3` | mentions=`8` | books=`4` | overfitting, Overfitting, over-fitting
- `Dynamic Mode Decomposition` | members=`3` | mentions=`7` | books=`1` | Dynamic Mode Decomposition, dynamic mode decomposition, Dynamic mode decomposition
- `nonnegative matrix factorization` | members=`3` | mentions=`6` | books=`2` | nonnegative matrix factorization, Nonnegative Matrix Factorization, non-negative matrix factorization
- `ROI` | members=`3` | mentions=`6` | books=`2` | ROI, 投资回报率, ROI (投资回报率)

## Recall Backlog

- head=`data` | type=`concept` | forms=`66` | unresolved_pairs=`2142` | objective data, subjective data, telemetry data, categorical data, quantitative data, ordinal data, qualitative data, continuous data
- head=`model` | type=`concept` | forms=`64` | unresolved_pairs=`2007` | reduced-order model, G(n, p) model, Kano model, car handling model, Double Diamond model, Ising model, streaming model, topic model
- head=`algorithm` | type=`algorithm` | forms=`55` | unresolved_pairs=`1483` | Perceptron Algorithm, belief propagation algorithm, gappy sensor placement algorithm, Viterbi algorithm, agglomerative algorithm, Apriori algorithm, augmented Lagrangian multiplier algorithm, Boosting Algorithm
- head=`metric` | type=`concept` | forms=`47` | unresolved_pairs=`1076` | game metrics, gameplay metrics, player metrics, performance metrics, physiological metrics, user metrics, Build Integrity Metrics, community metrics
- head=`test` | type=`algorithm` | forms=`41` | unresolved_pairs=`815` | McNemar exact test, two-sample t-test, N-1 two-proportion test, permutation test, chi-square test, F-test, Fisher exact test, N-1 chi-square test
- head=`function` | type=`concept` | forms=`40` | unresolved_pairs=`779` | cost function, generating function, harmonic function, scale function, convex function, kernel function, loss function, measurement function
- head=`matrix` | type=`concept` | forms=`38` | unresolved_pairs=`695` | Hankel matrix, measurement matrix, adjacency matrix, assumptions-knowledge matrix, correlation matrix, covariance matrix, Data matrix, data matrix
- head=`variable` | type=`concept` | forms=`36` | unresolved_pairs=`626` | indicator variable, binary variable, independent variable, dependent variable, factor variable, independent variables, key variables, adaptively explored variables
- head=`system` | type=`concept` | forms=`34` | unresolved_pairs=`557` | dynamical systems, human sensory system, underdetermined system, wavelet system, Achievement systems, analytics systems, closed-loop system, conservative dynamical system
- head=`system` | type=`tool` | forms=`31` | unresolved_pairs=`462` | telemetry system, logging system, telemetry systems, auto-braking system, Autolog system, bug tracking system, developer-facing telemetry system, dossier system
- head=`method` | type=`algorithm` | forms=`30` | unresolved_pairs=`434` | first moment method, Benjamini-Hochberg method, Monte Carlo methods, POD-Galerkin method, second moment method, alternating directions method, Alternating Directions Method, area-based methods
- head=`space` | type=`concept` | forms=`28` | unresolved_pairs=`376` | association space, image space, instance space, white space, Adobe RGB color space, affine space, CMYK color space, column space
- head=`network` | type=`algorithm` | forms=`28` | unresolved_pairs=`370` | Deep Convolutional Neural Networks, Neural Networks, adaptive neural networks, Bayesian network, classification network, Convolutional neural network, Deconvolutional Network, Deep Belief Network
- head=`map` | type=`concept` | forms=`28` | unresolved_pairs=`366` | heat map, choropleth map, heat maps, importance map, proportional symbol map, choropleth maps, data map, data maps
- head=`process` | type=`process` | forms=`27` | unresolved_pairs=`350` | data-driven UX design process, human-centered design process, user research process, agile development processes, analytical process, branching process, data-driven UX design (3DUX) process, Data-Driven UX Design Process
- head=`model` | type=`algorithm` | forms=`26` | unresolved_pairs=`323` | generalized linear model, beta-binomial model, binomial model, G(n, p) model, Gaussian mixture model, reduced order models, balanced reduced-order model, binomial probability model
- head=`distribution` | type=`concept` | forms=`25` | unresolved_pairs=`299` | binomial distribution, t-distribution, normal distribution, Poisson distribution, exponential distribution, Gaussian distribution, standard normal distribution, chi-square distribution
- head=`design` | type=`concept` | forms=`25` | unresolved_pairs=`297` | UX design, factorial design, usability and UX design, user experience design, visual design, within-subjects design, behavioral design, between-subjects design
- head=`error` | type=`concept` | forms=`25` | unresolved_pairs=`296` | standard error, Type I error, Type II error, training error, least-square error, reconstruction error, true error, Type 1 error
- head=`analysi` | type=`algorithm` | forms=`24` | unresolved_pairs=`270` | principal component analysis, principal components analysis, statistical analysis, discriminant analysis, regression analysis, Robust Principal Component Analysis, Stochastic Frontier Analysis, archetypal analysis

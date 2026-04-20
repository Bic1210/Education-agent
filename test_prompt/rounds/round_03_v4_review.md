# round_03_v4_review

## 基本信息

- 抽取结果文件：`prompt_v4_eval_20260418_213200.jsonl`
- 评审结果文件：`round_03_v4_review_review_v1.jsonl`
- 抽取 Prompt 版本：`v4`
- 评审 Prompt 版本：`review_v1`
- 模型：`deepseek-reasoner`
- Base URL：`https://api.openai-proxy.org/v1`
- 评审条数：`8`

## 评审结论统计

- accept: 0
- revise: 7
- reject: 1

## 高频问题

- weak_definition: 9
- wrong_relation: 9
- missed_core_concept: 8
- low_value_entity: 4
- wrong_type: 3
- hallucinated_entity: 3
- duplicate_synonym: 3
- empty_extraction_suspect: 2

## 逐条摘要

- Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) | chunk 5 | revise | 抽取了部分核心概念，但存在知识混淆、错误定义和方向错误的问题，需要修正。
  - [medium] weak_definition | e7: indicator variable | 原文明确指出‘indicator variable’是‘binary variable’的同义词（指代同一事物），而非独立的两个概念。该定义虽然描述了其功能，但将其作为独立实体抽离，造成了知识点的冗余和混淆。
  - [high] wrong_relation | e7 -> e6 包含 | 关系方向错误且概念混淆。原文表述是‘a special form of categorical variable is a binary (yes/no or 0/1) variable, seen in ... — an indicator variable...’。这表明 binary variable 是一种特殊的 categorical variable，而 indicator variable 在此处等同于 binary variable。因此，不应有从 indicator variable 到 binary variable 的包含关系。它们应是同一事物的不同名称。
  - [medium] missed_core_concept | overall | 遗漏了原文中的‘measured or counted data’这一概念。原文明确将‘measured or counted data’与‘categorical data’并列（e.g., duration and price...），它是一个重要的数据类型节点。
- Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) | chunk 6 | revise | 存在实体定义不精确、关系原文支持度弱以及遗漏关键术语等问题
  - [medium] weak_definition | e1 (箱线图) | 定义‘通过四分位数等快速可视化数据分布的图形’不完整且不精确。原文明确定义箱线图为Tukey引入的、可视化数据分布的‘快速方法’，并详细说明了其构成（箱体代表25/75百分位数，中位线，须线等）。当前定义丢失了‘quick way to visualize’的核心教学点，且‘等’字含糊，不符合原文描述的特定结构。
  - [medium] missed_core_concept | overall | 明显遗漏了原文‘KEY TERMS FOR EXPLORING THE DISTRIBUTION’标题下明确列出的核心术语‘Density plot’，原文已给出定义：‘A smoothed version of the histogram, often based on a kernal density estimate.’。这应作为一个独立节点被抽取。
  - [low] wrong_type | e6 (四分位数), e7 (十分位数) | 将‘四分位数’和‘十分位数’的类型定义为‘concept’虽然可以接受，但它们在统计中更常被视作‘百分位数’的特定类型或子类。原文中描述它们为‘common to report...’，并直接与百分位数关联。将它们作为更具体类型的‘statistical_measure’或明确与‘百分位数’建立子类关系可能更准确。但考虑到原文以‘concept’抽取整体术语，此项问题严重度较低。
- Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) | chunk 7 | reject | 抽取结果绝大部分为无原文支持的幻觉概念，完全偏离段落主旨。
  - [high] hallucinated_entity | 频率表 | 原文中并未出现‘频率表’或'frequency tables'，该实体是完全虚构的。
  - [high] hallucinated_entity | 百分位数 | 原文仅提及‘percentiles’，但并未展开作为核心概念介绍，其在表格中被提及是与‘quartiles’和‘deciles’并列，作为‘equal-count bins’的例子，并非当前段落讨论的‘equal-size bins’方法的实体。将其作为独立概念抽取属于过度推断。
  - [high] weak_definition | 区间 | 实体“区间”(bin)被识别，但其定义为空，教学价值为零。
- Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) | chunk 8 | revise | 抽取结果遗漏了多个核心概念，部分定义依据不足，关系抽取不完整且错误。
  - [high] missed_core_concept | overall | 原文明确提到了多个核心概念，如‘statistical moments’、‘location’、‘variability’、‘skewness’、‘kurtosis’、‘boxplot’、‘frequency histogram’、‘mode’、‘expected value’，但抽取结果完全未包含这些，对构建课程图谱是重大遗漏。
  - [high] wrong_relation | ‘e1’ 与 ‘e2’ 的‘可视化’关系 | 原文描述‘A histogram is a way to visualize a frequency table’，这是一种方式（is a way to），但抽取为直接的‘可视化’关系，过于概括且方向可能引起误解。更精确的关系应该是‘is a way to visualize’。
  - [high] missed_core_concept | frequency histogram | 原文在‘KEY IDEAS’中明确区分了‘frequency histogram’，并给出了定义。它是histogram的一种具体类型，应是独立节点。
- 可解释人工智能导论 (杨强 等) | chunk 5 | revise | 抽取结果存在幻觉实体、关系误读、遗漏核心概念以及定义质量差的问题。
  - [high] hallucinated_entity | e2（信任度） | 原文中的“信任度”是在特定实验情境中出现的、用于佐证可解释性价值的“评测指标”或“数据”，并非一个核心概念实体。抽取其为节点会混淆概念与度量指标。
  - [high] wrong_relation | 关系：可解释性 应用于 信任度 | 原文阐述“了解……决策机制，是提升……信任度的重要方法”，这是阐述可解释性对信任的作用或目的，并非“应用于”这种工具-用途的范畴关系。“应用于”关系是模型幻觉，原文并无支持。
  - [high] wrong_relation | 关系：主动干预 应用于 虚假关系；反事实推理 应用于 虚假关系 | 原文描述“为了从可能存在虚假关系的概率关联中进一步甄别出真正的因果关系，需要……主动干预实验……并运用反事实推理去伪存真”。这表明“主动干预”和“反事实推理”是用于“甄别因果关系”或处理“概率关联”（关联分析）的方法，而不是直接“应用于”虚假关系本身。关系方向与性质均误读。
- 可解释人工智能导论 (杨强 等) | chunk 6 | revise | 抽取基本准确，但存在一些冗余、定义不清和关系方向问题，且遗漏了更重要的监管动因和风险背景。
  - [medium] duplicate_synonym | e1 与 e2 | 原文中“可信赖的人工智能”和“可解释的人工智能”是作为同一目标的不同表述或直接相关，但抽取结果将其视为包含关系（e1包含e2），这导致了同义/紧密相关概念的重复和不必要的层级划分，教学上可能引起混淆。
  - [low] weak_definition | e2, e3, e4 | e2的定义“是可信赖的人工智能的一个核心方面”依赖于e1，且原文中对e2的定义更宽泛（例如第1.2.2节提及的三层分类）；e3和e4的定义虽然与原文内容基本一致，但均引用了图表（例如“解释者(Explainer)”、“解释受众(Explainee)”是图1-2的标注文字），在知识图谱中作为独立节点的教学价值相对较弱，更适合作为属性或关系（如“具有解释者”）。
  - [high] missed_core_concept | overall | 原文段落主要论述“人工智能系统未能获得信任”的三大原因（数据偏见、模型错误、决策不透明）以及监管要求，这些是“可信赖/可解释AI”的背景和动因。抽取结果完全遗漏了这些核心背景概念，如“数据偏见”、“模型鲁棒性/安全性”、“决策透明度”、“监管要求（如欧盟原则、中国金融规划）”等，而这些是理解“可解释AI”必要性的关键前置知识。
- 可解释人工智能导论 (杨强 等) | chunk 7 | revise | 抽取实体定义基本正确，但存在多个同义词、定义边界不清、价值低节点、重要遗漏和方向错误的关系项。
  - [medium] duplicate_synonym | e1，e2, e3等包含相同含义的重复元素 | 原文中 '解释者'、'解释受众' 与 '可解释AI' 中的描述存在内容重叠，特别是 '可解释AI'定义中已包含了沟通交流的对象，从知识图谱的抽象层次看，'解释者'、'解释受众'的抽象度低于'可解释AI'，在实际教学中可合并或重新归类，以清晰反映层次结构。
  - [high] wrong_relation | relations 为空 | 原文明确描述了多对关系，如 '可解释AI' 包含 '信任' 和 '解释'，'解释受众' 包含 '开发者'、'使用者/受影响者'、'监管者'，'解释' 包含'算法的透明度与简单性'等范畴。抽取结果遗漏了这些核心关系结构，使得图谱失去关键教学意义。
  - [low] weak_definition | e6，e7, e8定义相对正确，但缺少原文中一些重要限定 | 定义表述有些笼统，可更精确地体现原文细节。例如 e6 定义未提及通过 '计量算法的输入特征对于决策的影响' 来实现透明度和简单性。e8 定义未明确原文中 '提出预测结果的正当性' 这一关键点。
- 可解释人工智能导论 (杨强 等) | chunk 8 | revise | 抽取结果存在实体定义不准、类型错误、关系弱支持和核心遗漏等问题
  - [high] wrong_type | e8， e9， e10 | 原文中“线性回归”、“逻辑回归”、“决策树”在上下文（图1-8不同机器学习模型的准确率与可解释性比较）是作为“机器学习模型”的例子被讨论，目的是比较其“准确率”与“可解释性”。原文并未将它们定位为“算法”这一独立节点类型，而是作为一类“具有较强可解释性的模型”的举例。在知识图谱中，更适合作为“机器学习模型”的属性或例子，而非独立的算法节点。当前归类偏离了原文教学重点。
  - [high] weak_definition | e5 | 实体“可解释性方法”的定义空泛（“用于解释人工智能系统决策或预测的方法”），这是从实体名称直接推断的，未包含原文中该段落讨论的核心评测维度（如客观性、简单易懂性等是其评测指标）。这个定义未能帮助学生理解其在当前章节语境下的具体内涵。
  - [high] missed_core_concept | overall | 遗漏了核心概念“可解释AI”（或“可解释人工智能”），这是本节的核心主题，也是标题。原文明确提到“可解释AI相关的研究工作”、“可解释AI的重要性”、“对可解释AI的研究愈加重视”。这是必须抽取的核心节点。

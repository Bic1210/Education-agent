# round_01_v2_review

## 基本信息

- 抽取结果文件：`prompt_v2_eval_20260418_204626.jsonl`
- 评审结果文件：`round_01_v2_review_review_v1.jsonl`
- 抽取 Prompt 版本：`v2`
- 评审 Prompt 版本：`review_v1`
- 模型：`deepseek-reasoner`
- Base URL：`https://api.openai-proxy.org/v1`
- 评审条数：`8`

## 评审结论统计

- accept: 0
- revise: 6
- reject: 2

## 高频问题

- wrong_relation: 10
- missed_core_concept: 7
- duplicate_synonym: 5
- weak_definition: 5
- wrong_type: 4
- redundant_relation: 4
- low_value_entity: 3
- wrong_direction: 3

## 逐条摘要

- Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) | chunk 5 | revise | 抽取内容准确但价值不高且遗漏核心，需修订 prompt 以提升教学质量。
  - [medium] missed_core_concept | overall | 原文明确提到了 'categorical data'、'binary variable'、'indicator variable'、'unstructured data' 等核心概念，这些对理解数据类型至关重要，但抽取结果完全遗漏。
  - [low] low_value_entity | feature, outcome, record | 这三个实体（feature, outcome, record）的定义虽然正确，但它们是数据科学中最基础、几乎不言自明的术语，作为独立知识图谱节点教学价值有限，容易使图谱冗余。
  - [low] wrong_type | rectangular data | 'rectangular data' 的类型被标注为 'concept'，但原文上下文更倾向于它是一种数据结构或数据格式。在知识图谱中，将其定义为 'data_format' 或 'data_structure' 类型可能更准确，便于与 'unstructured data' 等概念形成对比关系。
- Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) | chunk 6 | reject | 抽取结果严重不忠于原文，包含较多臆想、重复和误读的关系，同时遗漏了核心概念和明确的原文关系。
  - [high] hallucinated_entity | 方差 | 原文段落只提到了‘standard deviation’，并未提及‘variance’（方差）这个概念。‘方差’在此是模型臆想出来的实体。
  - [high] duplicate_synonym | 分位数 | 原文明确指出‘Percentiles’和‘quantiles’是同义词，但在‘KEY TERMS’部分被合称为‘Percentiles and Boxplots’，模型却将其拆分为‘e5 百分位数’和‘e6 分位数’两个节点，造成同义重复。
  - [high] missed_core_concept | overall | 原文‘KEY TERMS FOR EXPLORING THE DISTRIBUTION’下明确列出了‘Boxplot’, ‘Frequency table’, ‘Histogram’, ‘Density plot’，并包含了‘Synonyms’说明。模型遗漏了该节标题作为一个重要的结构性概念或上下文，也未完全涵盖此列表的上下文意义。此外，原文中‘IQR’（四分位距）作为重要概念在代码和分析中多次出现，未被抽取。
- Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) | chunk 7 | reject | 抽取结果完全空置，但原文段落包含明确、核心的教学知识点，遗漏严重。
  - [high] missed_core_concept | overall | 原文明确讨论了“分箱”(binning)这一核心数据科学概念，包括等宽分箱、空箱的重要性、分箱大小的权衡（过于宽泛或精细的弊端），并提及频率表和百分位数，这些都是可抽取的教学概念。
  - [medium] empty_extraction_suspect | overall | 段落中夹杂了人口数据和州名缩写，但后半部分是连贯的关于分箱的统计教学文本，全部忽略是不合理的。
- Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) | chunk 8 | revise | 抽取存在事实错误、实体混淆和严重漏抽，教学质量差
  - [high] hallucinated_entity | frequency histogram | 原文提到‘A frequency histogram plots frequency counts...’，但在该段第一句明确说明‘A histogram is a way to visualize a frequency table’，并在Key Ideas中重申‘A frequency table is a tabular version...’。抽取结果将‘frequency histogram’作为独立核心实体，并与‘frequency table’和‘histogram’建立关系，这些关系原文并未支持，且‘frequency histogram’与‘histogram’在教学上是混淆的。
  - [high] wrong_relation | 关系 '应用于' 和 '衍生' | 关系‘e1应用于e2’(频率直方图应用于频率表)：原文明确指出‘A histogram is a way to visualize a frequency table’，并且‘A frequency table is a tabular version...’，这表明是直方图可视化频率表（或频率表是直方图的表格版本），而非频率直方图‘应用于’频率表。关系‘e1衍生e3’(频率直方图衍生直方图)：这在逻辑和原文上都不成立，原文并没有这种衍生关系的表述。关系‘e4衍生e3’(密度图衍生直方图)：原文说‘A density plot can be thought of as a smoothed histogram’，这是比喻或性质说明，并非‘衍生’关系（衍生通常指从A产生B）。这些关系都属于过度解读或方向错误。
  - [high] missed_core_concept | overall | 原文段落后半部分和Key Terms明确提到了多个核心概念未被抽取，包括：‘Statistical moments’、‘Location’、‘Variability’、‘Skewness’、‘Kurtosis’、‘Density estimation’、‘Kernel density estimate’、‘Mode’、‘Expected value’。这些是数据探索和描述统计中的基础概念，教学价值高，不应漏掉。
- 可解释人工智能导论 (杨强 等) | chunk 5 | revise | 抽取结果存在定义不准确、原文支持弱、核心概念遗漏及关系方向错误等问题。
  - [high] missed_core_concept | overall | 原文明确提出了决策机制存在‘机器学习的应用缺陷’和‘人工智能系统未能满足监管要求’三方面差距，以及‘关联分析’、‘虚假关系’等核心概念，但抽取结果全部遗漏。
  - [high] wrong_direction | 关系 'e6 包含 e4' 和 'e6 包含 e5' | 原文中Judea Pearl的理论是‘因果推理学习’包含‘主动干预’和‘反事实推理’等方法，但这是一种理论层面的‘包括’或‘涵盖’，而不是‘因果推理’（概念）在实体或逻辑上‘包含’‘主动干预’（算法）和‘反事实推理’（算法），这种关系定义在知识图谱中容易造成歧义。原文关系是弱支持且方向易误导。
  - [medium] weak_definition | e6: 因果推理 | 定义‘Judea Pearl教授概括的从低到高的认知层次理论’过于空泛和同义反复。原文指出了一个三层认知层次理论，而‘因果推理’是更高层次的目标或能力，定义未能清晰说明其内涵及其与关联、干预的区别。
- 可解释人工智能导论 (杨强 等) | chunk 6 | revise | 实体定义部分准确，但整体抽取结果严重不完整，遗漏了核心关系且部分实体属于弱实体或同义词。
  - [high] missed_core_concept | overall | 原文大篇幅讨论人工智能（尤其是AI系统）的风险（如偏见、安全、不透明）和监管要求（如欧盟、中国的原则），这是提出“可解释人工智能”需求的重要背景，但抽取结果未包含任何“风险”或“监管要求”相关的核心概念。
  - [high] wrong_relation | relations 字段为空 | 原文明确阐述了概念间的因果关系和层次关系。例如，‘深度神经网络’是‘黑盒’的，‘不透明’导致‘缺乏信任’和‘解释需求’。‘可解释AI的层次’包含‘解释者’和‘解释受众’。抽取结果为空的`relations`不符合原文内容。
  - [medium] low_value_entity | e3: 预训练神经网络 | 原文中‘预训练神经网络’仅是作为‘深度神经网络’下‘超规模’的例子（如BERT、GPT-3）出现，其本身并非段落讨论的核心独立概念，而是‘深度神经网络’的一个属性/子类。作为独立节点价值较低且与e2有包含关系未体现。
- 可解释人工智能导论 (杨强 等) | chunk 7 | revise | 抽取了多个核心概念，但存在关系方向错误、过度概括、定义不精确以及漏抽重要关系等问题。
  - [medium] wrong_relation | source: e1, target: e2, relation: 包含 | 原文段落并未明确表述“可解释人工智能”概念“包含”“信任”这个概念。原文表述“涉及两个重要的基本概念：信任与解释”，是并列和涉及关系，并非包含关系。
  - [medium] wrong_relation | source: e1, target: e3, relation: 包含 | 同上，“可解释人工智能”并不“包含”“解释”这个概念，原文是并列提及的两个基本概念。
  - [low] weak_definition | e1：可解释人工智能 | 定义引用了原文，基本准确，但可能缺少最终的目标句“以取得人类信任，同时满足各类应用场景对智能体决策机制的监管要求”。
- 可解释人工智能导论 (杨强 等) | chunk 8 | revise | 抽取的实体存在严重类型误判和关系虚构，定义质量一般，未能抓住段落教学核心。
  - [high] wrong_type | e3, e4, e5, e6, e18 | “客观性”、“解释结果的简单易懂性”、“互洽性”、“计算效率”是评测维度或指标，原文并未将其作为概念节点，而是“评测维度”的属性。将指标/维度作为独立概念节点会污染知识图谱，并误导学生。 “机器学习模型的可解释性”是一个宽泛的话题名称或短语，并非实体，原文是指某些模型“本身被认为是具有较强可解释性的”。
  - [high] wrong_relation | e11, e9 | 原文仅说明逻辑回归“是在线性回归的基础上”通过logit函数映射。这描述了一种继承或扩展关系，而“衍生”过于宽泛且不准确。原文提到模糊逻辑用于模拟神经元，使规则决策更灵活，是一种“利用”或“结合”的关系，并非“基于自动生成规则的推理机制解释”“衍生”了“模糊逻辑”（后者是更底层的逻辑系统）。
  - [medium] redundant_relation | e1->e13 | 关系“依赖”缺乏原文强支持且过于宽泛。原文是“随着深度学习的再度兴起，人们对可解释AI的研究愈加重视”，这是一种趋势描述（时间伴随），并非“可解释AI”实体“依赖”于“深度学习”实体。这种关系在教学上容易造成因果或前提误解。

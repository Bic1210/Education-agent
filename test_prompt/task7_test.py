import json
from openai import OpenAI

# ===== 填入你的 API Key =====
API_KEY = "此处粘贴世界上最帅的彦杰的api，我用的是close ai的deepseek key，接口是openai的，如果不兼容到时候你自己改一下"
# ============================

client = OpenAI(
    base_url="https://api.openai-proxy.org/v1",
    api_key=API_KEY
)

PROMPT_TEMPLATE = """你是一个专业的知识图谱构建助手，擅长从教材中提取结构化知识。

请从以下教材段落中提取知识图谱，要求：

1. 只提取该段落中明确出现的概念，不要推断或补充段落没有提到的内容
2. 实体名称使用段落中的原始表述（不要翻译或改写）
3. 只返回 JSON，不要任何解释性文字
4. 如果多个词是同义词，只保留最常用的那一个实体，其余不要提取
5. 不要提取书中举例用的具体数据（如表格列名、数值、人名、地名）

实体类型（type）只能是以下五种之一：
- concept   核心概念（如：机器学习、假设检验）
- algorithm 算法或方法（如：K-means、线性回归）
- task      任务或应用场景（如：图像分类、推荐系统）
- process   流程或步骤（如：数据预处理流程）
- tool      工具或框架（如：PyTorch、scikit-learn）

关系类型（relation）只能是以下六种之一：
- 包含       A 包含 B（上下位关系）
- 依赖       理解或使用 A 需要先掌握 B
- 应用于     A 被用在 B 场景中
- 衍生       B 由 A 发展而来
- 前置条件   学习 A 之前必须掌握 B
- 对比       A 与 B 是同类方法的比较（注意：同义词不是对比，对比是指两种不同方法或概念的比较）

输出格式：
{{
  "entities": [
    {{"id": "e1", "name": "实体名称", "type": "concept", "definition": "基于原文内容的简短定义，不超过50字，不能只是翻译实体名称本身"}}
  ],
  "relations": [
    {{"source": "e1", "target": "e2", "relation": "包含"}}
  ]
}}

段落来源：《{book_title}》- {chapter_title}

段落内容：
{text}"""


def extract_graph(chunk: dict) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        book_title=chunk["book_title"],
        chapter_title=chunk["chapter_title"],
        text=chunk["text"]
    )

    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()

    # 去掉 AI 有时会加的 ```json ``` 包裹
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    return json.loads(content)


# ===== 读取一条语料做测试 =====
CORPUS_FILE = "corpus/per_book/04_Practical Statistics for Data Scientists 50 Essential Concepts (Peter Bruce, Andrew Bruce) (z-library.sk, 1lib.sk, z-lib.sk).json"

with open(CORPUS_FILE, encoding="utf-8") as f:
    corpus = json.load(f)

# 取第5条（跳过前几条可能是版权页/目录的段落）
chunk = corpus[4]

print("=" * 60)
print(f"书名：{chunk['book_title'][:50]}")
print(f"章节：{chunk['chapter_title']}")
print(f"段落字数：{chunk['char_count']}")
print(f"段落内容预览：{chunk['text'][:200]}")
print("=" * 60)
print("正在调用 DeepSeek...")

result = extract_graph(chunk)

print("\n【提取结果】")
print(json.dumps(result, ensure_ascii=False, indent=2))

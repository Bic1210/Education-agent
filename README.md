# AI 知识图谱与智能问答系统

> **项目定位**：将教材书籍自动处理为结构化语料库，再通过 LLM 抽取知识图谱，最终支持智能问答与可视化。
>
> 本 README 覆盖**模块一**（书籍处理 → 语料库）的完整说明，以及**模块二**（LLM 抽取 → 知识图谱）的接口约定，供后续同学对接使用。

---

## 目录

1. [项目结构](#项目结构)
2. [环境配置](#环境配置)
3. [快速开始](#快速开始)
4. [功能模块说明](#功能模块说明)
5. [数据格式规范](#数据格式规范)
6. [API 接口文档](#api-接口文档)
7. [模块二对接说明](#模块二对接说明)
8. [常见问题](#常见问题)

---

## 项目结构

```
EducationAgent/
│
├── 📁 Functional_block_testing/     # 离线处理功能模块（单独运行）
│   ├── 01_install.bat               # 依赖安装脚本（首次运行）
│   ├── 02_run_ocr_v5.py             # PDF → TXT 转换（支持扫描版/自定义字体PDF）
│   └── 03_parse_and_build_corpus_v5.py  # TXT → 标准化语料库 JSON
│
├── 📁 input_pdfs/                   # 放置待转换的 PDF 文件（手动放入）
├── 📁 output_txts/                  # 离线转换输出的 TXT 文件
├── 📁 corpus/                       # 离线生成的语料库 JSON
│
├── 📁 knowledge-platform/           # React 前端
│   ├── src/
│   │   └── App.jsx                  # 主界面组件
│   ├── package.json
│   └── vite.config.js
│
├── 📁 data/                         # 网页后端运行时数据（自动生成，勿手动修改）
│   ├── uploads/                     # 网页上传的原始文件
│   ├── output_txts/                 # 网页处理后的 TXT
│   ├── corpus/                      # 网页生成的语料库 JSON
│   └── graphs/                      # 网页生成的图谱 JSON
│
└── server.py                        # Flask 后端 API 服务
```

---

## 环境配置

### 系统要求

- Python 3.9+
- Node.js 18+（前端）
- CUDA 11.x+（可选，GPU 加速 OCR）

### 第一步：安装 Python 依赖

```bash
# 方式A：直接运行安装脚本（Windows）
01_install.bat

# 方式B：手动安装
pip install flask flask-cors pymupdf pillow numpy tqdm

# OCR 支持（处理扫描版 PDF 时需要）
pip install paddlepaddle-gpu -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install paddleocr
```

### 第二步：安装前端依赖

```bash
cd knowledge-platform
npm install
```

---

## 快速开始

### 方式一：网页界面（推荐）

```bash
# 终端1：启动后端
python server.py
# 访问 http://localhost:5000 确认运行

# 终端2：启动前端
cd knowledge-platform
npm run dev
# 访问 http://localhost:5173
```

在网页中：
1. 点击上传区域，拖入 PDF 或 TXT 文件
2. 点击**生成语料库**按钮（自动完成 PDF→TXT→语料库全流程）
3. 在"标准化语料库"标签页查看、编辑切分结果
4. 点击**下载**导出 JSON，供模块二使用

### 方式二：离线脚本处理（处理大量书籍时推荐）

```bash
# 步骤1：将 PDF 文件放入 input_pdfs/ 目录

# 步骤2：PDF → TXT（支持扫描版）
cd Functional_block_testing
python 02_run_ocr_v5.py
# 输出：../output_txts/*.txt

# 步骤3：TXT → 标准化语料库
python 03_parse_and_build_corpus_v5.py
# 输出：../corpus/corpus.json 和 ../corpus/corpus_stats.csv
```

---

## 功能模块说明

### `02_run_ocr_v5.py` — PDF 转 TXT

| 功能 | 说明 |
|------|------|
| 文字型 PDF | 直接提取（速度快，质量高） |
| 扫描版 PDF | PaddleOCR 识别（需安装 paddleocr） |
| 自定义字体 PDF | 自动检测乱码，降级为 OCR |
| 双栏版式 | 自动检测并分栏处理 |
| 中英文混合 | 统一处理，无需手动指定语言 |

**配置项**（脚本顶部）：

```python
INPUT_DIR  = "./input_pdfs"    # PDF 输入目录
OUTPUT_DIR = "./output_txts"   # TXT 输出目录
USE_GPU    = True              # 是否使用 GPU 加速
```

**输出 TXT 格式**：

```
文件名：书名.txt
原始文件：原PDF文件名.pdf
转换时间：2026-04-15 14:00:00
============================================================

--- 第 1 页 / Page 1 [text] ---
正文内容...

--- 第 2 页 / Page 2 [ocr] ---
...
```

---

### `03_parse_and_build_corpus_v5.py` — 语料库构建

完成任务 2~5：章节识别 → 打标签 → 文本清洗 → 输出 JSON。

| 功能 | 说明 |
|------|------|
| 章节识别 | 支持中英文多种格式（第N章 / Chapter N / N.N Title 等） |
| 多行标题合并 | 修复 OCR 断行导致的标题被拆散问题 |
| 页眉过滤 | 自动识别并过滤重复页眉 |
| 文本清洗 | 去除版权声明、参考文献、页码等噪声 |
| OCR 质量检测 | 质量差时自动按页切分，避免乱码影响 |
| 编号前缀去重 | 合并同节因 OCR 产生的碎片段落 |

**配置项**：

```python
INPUT_DIR  = "./output_txts"   # TXT 输入目录
OUTPUT_DIR = "./corpus"        # 语料库输出目录
MIN_CHUNK_CHARS = 150          # 段落最小字符数
MAX_CHUNK_CHARS = 6000         # 段落最大字符数
```

**运行输出**：

```
corpus/
├── corpus.json          # 所有书籍语料库（合并）
└── corpus_stats.csv     # 每本书的统计摘要
```

---

### `server.py` — 后端 API

Flask 服务，整合了以上两个脚本的核心逻辑，供网页调用。

- 端口：`5000`
- 书籍数据存储在内存（`books_db`），重启后清空
- 文件持久化在 `data/` 目录

---

### `knowledge-platform/src/App.jsx` — 前端界面

React 单页应用，包含三个主要标签页：

| 标签页 | 功能 |
|--------|------|
| 原书籍 | 上传文件，查看原始 TXT 内容 |
| 标准化语料库 | 查看切分结果，支持手动编辑每段文字 |
| 结构化知识图谱数据 | 查看/生成图谱（当前为关键词提取演示） |

---

## 数据格式规范

### 标准化语料库（`corpus.json`）

每条记录代表一个文本段落，是模块二 LLM 抽取的输入单元。

```json
{
  "book_id": "book_01",
  "book_title": "书名",
  "language": "zh",
  "source_file": "原始文件名.txt",
  "chapter_title": "第3章 假设检验",
  "chapter_level": "chapter",
  "chunk_index": 42,
  "total_chunks": 180,
  "text": "段落正文内容，最少150字符，最多6000字符...",
  "char_count": 1234,
  "created_at": "2026-04-15 14:00:00"
}
```

**`chapter_level` 枚举值**：

| 值 | 含义 |
|----|------|
| `part` | 大部分（Part I） |
| `chapter` | 章（第1章 / Chapter 1） |
| `section` | 节（1.1） |
| `subsection` | 小节（1.1.1） |
| `appendix` | 附录 |
| `intro` | 前言/导言 |

---

### 知识图谱数据格式（模块二输出规范）

> **后续同学请严格遵循此格式输出**，模块三可视化直接读取。

#### 实体节点（entities）

```json
{
  "id": "e_001",
  "name": "A/B 测试",
  "aliases": ["A/B Test", "AB测试", "对照实验"],
  "type": "concept",
  "definition": "通过对比两种方案衡量效果差异的实验方法",
  "source_books": ["数据驱动设计", "Practical Statistics"],
  "source_chunks": ["book_01_chunk_42", "book_03_chunk_17"]
}
```

**`type` 枚举值**：

| 值 | 含义 | 示例 |
|----|------|------|
| `concept` | 核心概念 | 机器学习、假设检验 |
| `algorithm` | 算法/方法 | SVD、K-means |
| `task` | 任务/应用场景 | 图像分类、推荐系统 |
| `process` | 流程/步骤 | 数据预处理流程 |
| `tool` | 工具/框架 | PyTorch、scikit-learn |

#### 关系边（relations）

```json
{
  "id": "r_001",
  "source": "e_001",
  "target": "e_002",
  "relation": "依赖",
  "weight": 0.8,
  "source_book": "数据驱动设计",
  "source_chunk": "book_01_chunk_42"
}
```

**`relation` 枚举值**：

| 值 | 含义 |
|----|------|
| `包含` | 上下位关系（A 包含 B） |
| `依赖` | A 的实现/理解需要 B |
| `应用于` | A 被应用在 B 场景 |
| `衍生` | B 由 A 发展而来 |
| `前置条件` | 学习 A 之前需要掌握 B |
| `对比` | A 与 B 是同类方法的对比 |

#### 完整图谱文件结构

```json
{
  "entities": [...],
  "relations": [...],
  "book_count": 10,
  "entity_count": 320,
  "relation_count": 580,
  "created_at": "2026-04-20 10:00:00"
}
```

---

## API 接口文档

后端运行在 `http://localhost:5000`。

### 上传文件

```
POST /api/upload
Content-Type: multipart/form-data
Body: file=<PDF或TXT文件>

返回: { id, name, file, size, pages, ext, status: "uploaded" }
```

### 获取书籍列表

```
GET /api/books
返回: [{ id, name, file, size, pages, status, ... }, ...]
```

### 生成语料库

```
POST /api/process/corpus/<book_id>
返回: { ok, book, corpus: [...], stats: { total_chunks, total_chars, language, levels } }
```

### 获取语料库

```
GET /api/corpus/<book_id>
返回: { corpus: [...] }
```

### 编辑语料段落

```
POST /api/corpus/<book_id>/edit
Body: { chunk_index: 42, text: "修改后的文字" }
返回: { ok: true }
```

### 生成知识图谱

```
POST /api/process/graph/<book_id>
Body: { api_key: "DeepSeek API Key（可选）" }
返回: { ok, graph: { entities, relations } }
```

### 生成全局图谱

```
POST /api/process/global-graph
Body: { book_ids: ["id1", "id2", ...] }
返回: { ok, graph: { entities, relations, book_count } }
```

### 下载文件

```
GET /api/download/<book_id>/corpus   # 下载语料库 JSON
GET /api/download/<book_id>/graph    # 下载图谱 JSON
```

### 删除书籍

```
DELETE /api/books/<book_id>
返回: { ok: true }
```

---

## 模块二对接说明

> 本节专供负责任务 7~13 的同学阅读。

### 你的输入

语料库 JSON，每条记录是一个文本段落（见上方数据格式）。

获取方式：
1. 从网页界面点击**下载**按钮，得到 `corpus.json`
2. 或调用 `GET /api/corpus/<book_id>` 接口直接获取
3. 或读取 `corpus/corpus.json`（离线脚本生成的合并版）

### 你的输出

严格按照上方**知识图谱数据格式**输出 `graph.json`，包含 `entities` 和 `relations` 两个列表。

完成后，调用以下接口将图谱写入系统，前端可视化会自动加载：

```python
import requests, json

graph_data = json.load(open("your_graph.json"))
# 将图谱挂载到某本书（或用 global-graph 接口合并多本）
requests.post(
    "http://localhost:5000/api/process/global-graph",
    json={"book_ids": ["book_id_1", "book_id_2"]}
)
```

### 推荐开发流程

```
任务7：设计 LLM prompt（输入：corpus.json 的一条记录 → 输出：entities + relations）
   ↓
任务8：用 1-2 本书的语料库试跑，人工评估抽取质量
   ↓
任务9：根据评估迭代 prompt，直到质量达标
   ↓
任务10：写批量脚本，循环处理所有书籍的所有段落
   ↓
任务11：实体去重合并（"ML"/"机器学习"/"machine learning" → 同一节点）
   ↓
任务12：评估去重效果，人工抽检
   ↓
任务13：输出最终 graph.json，供模块三可视化使用
```

### DeepSeek API 调用示例

```python
import requests

def extract_graph_from_chunk(chunk: dict, api_key: str) -> dict:
    """从一个语料段落抽取实体和关系"""
    prompt = f"""
    请从以下教材段落中提取知识图谱，严格按 JSON 格式输出：
    {{
      "entities": [
        {{"id": "e1", "name": "实体名", "type": "concept/algorithm/task/process/tool",
          "definition": "一句话定义"}}
      ],
      "relations": [
        {{"source": "e1", "target": "e2",
          "relation": "包含/依赖/应用于/衍生/前置条件/对比"}}
      ]
    }}
    
    要求：
    - 只提取该段落明确提及的概念，不要推断
    - 实体名使用段落中的原始表述
    - 只返回 JSON，不要其他文字
    
    段落来源：《{chunk['book_title']}》 - {chunk['chapter_title']}
    
    段落内容：
    {chunk['text'][:2000]}
    """
    
    resp = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        json={"model": "deepseek-chat",
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.1},
        timeout=60
    )
    content = resp.json()["choices"][0]["message"]["content"].strip()
    # 去掉可能的 ```json ``` 包裹
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)
```

---

## 常见问题

**Q：上传 PDF 后生成语料库全是空段落？**

A：该 PDF 使用了自定义字体编码，无法直接提取文字。解决方法：
1. 将 PDF 放入 `input_pdfs/`
2. 运行 `python Functional_block_testing/02_run_ocr_v5.py`（需安装 paddleocr）
3. 将生成的 TXT 文件上传到网页，而非原 PDF

**Q：书名在生成语料库后变了？**

A：已在最新版 `server.py` 修复。书名始终使用上传时的原始文件名，不会被正文内容覆盖。

**Q：Windows 上报错 `[Errno 22] Invalid argument`？**

A：已在最新版修复。文件路径中的特殊字符（冒号等）会自动替换为下划线。

**Q：OCR 速度很慢？**

A：确认已安装 GPU 版 PaddlePaddle（`paddlepaddle-gpu`）且 CUDA 正常。在 `02_run_ocr_v5.py` 中确认 `USE_GPU = True`。一般每页 OCR 约 1-3 秒（GPU），CPU 模式约 10-30 秒。

**Q：处理中文书籍效果差？**

A：中文书籍通常 OCR 识别准确率较高，但章节切分可能不准。可在 `03_parse_and_build_corpus_v5.py` 的调试模式下查看识别结果：
```python
builder.run_debug(Path("your_book.txt"))
```

**Q：重启 server.py 后书籍列表消失了？**

A：当前版本书籍元数据存在内存中，重启后需重新上传。语料库 JSON 文件保留在 `data/corpus/` 目录，不会丢失。后续版本计划改用 SQLite 持久化。

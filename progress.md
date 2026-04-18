# 知识图谱数据库 — 进度追踪

**项目**：AI 知识图谱与智能问答系统  
**更新日期**：2026-04-15  

---

## 模块一：书籍处理 → 标准化语料库（已完成）

### 任务完成状态

| 任务 | 描述 | 状态 | 负责人 |
|------|------|------|--------|
| 任务1 | PDF → TXT 转换（含扫描版OCR） | ✅ 完成 | 第一阶段 |
| 任务2 | 章节识别与文本切分 | ✅ 完成 | 第一阶段 |
| 任务3 | 段落打标签（来源标注） | ✅ 完成 | 第一阶段 |
| 任务4 | 文本清洗（噪声过滤） | ✅ 完成 | 第一阶段 |
| 任务5 | 输出标准化语料库 JSON | ✅ 完成 | 第一阶段 |
| 任务6 | 网页交互原型（上传/预览/编辑） | ✅ 完成 | 第一阶段 |

### 交付物

| 文件 | 路径 | 说明 |
|------|------|------|
| PDF→TXT 脚本 | `Functional_block_testing/02_run_ocr_v5.py` | 支持扫描版和自定义字体PDF |
| 语料库构建脚本 | `Functional_block_testing/03_parse_and_build_corpus_v5.py` | 章节识别+清洗+输出 |
| 后端服务 | `server.py` | Flask API，整合以上两个脚本 |
| 前端界面 | `knowledge-platform/src/App.jsx` | React 网页界面 |
| 依赖安装 | `01_install.bat` | 一键安装脚本 |

### 书籍处理状态

> 注意：书籍处理通过网页界面或离线脚本完成，状态以实际处理结果为准。
> 以下为截至 2026-04-15 的示例状态，请在交接时更新。

| 书名 | 语言 | PDF类型 | 处理方式 | 状态 | 段落数 | 字符数 |
|------|------|---------|---------|------|--------|--------|
| 数据驱动设计：A/B测试 | 中文 | 文字型 | 直接提取 | ✅ | ~180 | ~160K |
| Data-Driven Science | 英文 | 文字型 | 直接提取 | ✅ | ~211 | ~817K |
| Foundations of Data Science | 英文 | 自定义字体 | OCR | ✅ | ~209 | ~870K |
| Practical Statistics | 英文 | 文字型 | 直接提取 | ✅ | ~139 | ~484K |
| Quantifying Uncertainty | 英文 | 文字型 | 直接提取 | ✅ | ~175 | ~716K |
| Storytelling with Data | 英文 | 扫描版 | OCR | ✅ | ~91 | ~313K |
| *(待处理书籍)* | - | - | - | ⏳ | - | - |

---

## 模块二：LLM 抽取 → 知识图谱（待开始）

### 任务清单

| 任务 | 描述 | 状态 | 负责人 | 预计完成 |
|------|------|------|--------|---------|
| 任务7 | 设计 LLM 抽取 prompt | ⏳ 待开始 | - | - |
| 任务8 | 用 1-2 本书试跑，人工评估 | ⏳ 待开始 | - | - |
| 任务9 | 根据评估迭代 prompt | ⏳ 待开始 | - | - |
| 任务10 | 批量处理全部书籍 | ⏳ 待开始 | - | - |
| 任务11 | 实体去重合并 | ⏳ 待开始 | - | - |
| 任务12 | 评估去重效果 | ⏳ 待开始 | - | - |
| 任务13 | 输出最终结构化图谱数据 | ⏳ 待开始 | - | - |

### 模块二接收的输入

**语料库 JSON**，每条记录格式如下：

```json
{
  "book_id": "book_01",
  "book_title": "书名",
  "language": "zh",
  "source_file": "文件名.txt",
  "chapter_title": "第3章 假设检验",
  "chapter_level": "chapter",
  "chunk_index": 42,
  "total_chunks": 180,
  "text": "段落正文（150~6000字符）...",
  "char_count": 1234,
  "created_at": "2026-04-15 14:00:00"
}
```

获取方式：
1. 网页界面 → 选择书籍 → 点击**下载**按钮
2. 调用 `GET http://localhost:5000/api/corpus/<book_id>`
3. 读取 `corpus/corpus.json`（离线处理的合并版）

### 模块二需要输出的格式

实体节点：

```json
{
  "id": "e_001",
  "name": "A/B 测试",
  "aliases": ["AB测试", "A/B Test", "对照实验"],
  "type": "concept",
  "definition": "通过对比两种方案衡量效果差异的实验方法",
  "source_books": ["数据驱动设计"],
  "source_chunks": ["book_01_chunk_42"]
}
```

关系边：

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

完整输出文件结构：

```json
{
  "entities": [...],
  "relations": [...],
  "entity_count": 320,
  "relation_count": 580,
  "book_count": 10,
  "created_at": "2026-04-20 10:00:00"
}
```

**`type` 合法值**：`concept` / `algorithm` / `task` / `process` / `tool`

**`relation` 合法值**：`包含` / `依赖` / `应用于` / `衍生` / `前置条件` / `对比`

### 模块二写入系统的方式

完成抽取后，调用以下接口将图谱写入后端，前端可视化自动加载：

```python
import requests, json

# 将单本书的图谱写入
with open("your_graph.json") as f:
    graph = json.load(f)

# 方式一：通过 global-graph 接口合并写入
requests.post(
    "http://localhost:5000/api/process/global-graph",
    json={"book_ids": ["book_id_1", "book_id_2"]}
)

# 方式二：直接放到 data/graphs/global_graph.json（服务重启后加载）
```

---

## 技术栈总览

| 层 | 技术 | 说明 |
|----|------|------|
| PDF 提取 | PyMuPDF + PaddleOCR | 文字型直接提取，扫描版 OCR |
| 文本处理 | Python 3 + re | 章节识别、清洗、切分 |
| 后端 API | Flask + Flask-CORS | RESTful API |
| 前端 | React + Vite | 网页界面 |
| LLM 接口 | DeepSeek API | 知识抽取（模块二） |
| 数据存储 | JSON 文件 | 当前版本；后续可升级 SQLite |

---

## 已知限制与后续改进

| 问题 | 当前状态 | 建议改进 |
|------|---------|---------|
| 书籍数据重启丢失 | 存内存，重启清空 | 改用 SQLite 持久化 |
| OCR 速度慢 | GPU 约1-3秒/页 | 批量预处理，结果缓存 |
| 扫描版中文识别率 | 约85-90% | 尝试更高DPI或后处理 |
| 章节识别漏识 | 部分特殊格式未覆盖 | 上传文件后人工抽查并在网页编辑 |

---

## 联系与交接

- 模块一代码问题：查阅 `README.md` 或 `server.py` 注释
- 数据格式问题：以本文档"数据格式规范"章节为准
- API 问题：见 `README.md` 的 API 接口文档章节
- 如需修改后端逻辑：编辑 `server.py`，重启即生效（`python server.py`）

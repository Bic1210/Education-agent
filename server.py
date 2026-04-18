"""
知识图谱平台 — 后端 API 服务
Flask + OCR v5 + 语料库构建 v5

启动方式：
    pip install flask flask-cors pymupdf
    python server.py

注意：
- OCR 功能需要额外安装 paddleocr（处理扫描版PDF或自定义字体PDF时自动调用）
- 若未安装 paddleocr，无法提取内容的页面会输出为空（建议先用 02_run_ocr_v5.py 离线转换）
- DeepSeek API 需要填入你的 API Key
"""

import os
import re
import json
import uuid
import time
import traceback
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Optional

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# ============================================================
# Flask 应用
# ============================================================

app = Flask(__name__)
CORS(app)

BASE_DIR   = Path("./data")
UPLOAD_DIR = BASE_DIR / "uploads"
TXT_DIR    = BASE_DIR / "output_txts"
CORPUS_DIR = BASE_DIR / "corpus"
GRAPH_DIR  = BASE_DIR / "graphs"

for d in [UPLOAD_DIR, TXT_DIR, CORPUS_DIR, GRAPH_DIR]:
    d.mkdir(parents=True, exist_ok=True)

books_db: dict = {}   # { book_id: { id, name, file, size, pages, status, ... } }

# ============================================================
# PDF → TXT（同步 v5 逻辑）
# ============================================================

TEXT_EXTRACT_MIN_CHARS = 30


def _is_readable_text(text: str, min_ratio: float = 0.5) -> bool:
    """
    检查 get_text() 内容是否真正可读（非乱码）。
    某些 PDF 使用自定义 Type1 字体编码（无 ToUnicode），PyMuPDF 会提取乱码。
    用"可读字符占比"区分可用文字与乱码。
    """
    if not text:
        return False
    readable = sum(
        1 for c in text
        if ('A' <= c <= 'Z') or ('a' <= c <= 'z')
        or ('0' <= c <= '9')
        or ('\u4e00' <= c <= '\u9fff')
        or c in ' \t\n.,;:!?()-\'"'
    )
    return (readable / len(text)) >= min_ratio


def is_text_page(page) -> bool:
    """
    判断页面是否可直接提取文字（v5：同时验证可读性）。
    解决自定义字体 PDF 的乱码误判问题。
    """
    raw = page.get_text("text").strip()
    if len(raw) < TEXT_EXTRACT_MIN_CHARS:
        return False
    return _is_readable_text(raw)


def extract_text_page(page) -> str:
    """段落感知文字提取（rawdict 模式）"""
    import fitz
    data   = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    blocks = data.get("blocks", [])
    raw_lines = []
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            bbox   = line["bbox"]
            y_mid  = (bbox[1] + bbox[3]) / 2
            height = bbox[3] - bbox[1]
            text   = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
            if text:
                raw_lines.append({"y": y_mid, "x0": bbox[0], "h": height, "text": text})
    if not raw_lines:
        return ""
    raw_lines.sort(key=lambda l: (round(l["y"] / 3), l["x0"]))
    merged = []
    for line in raw_lines:
        if merged and abs(line["y"] - merged[-1]["y"]) < merged[-1]["h"] * 0.5:
            merged[-1]["text"] += " " + line["text"]
        else:
            merged.append(dict(line))
    result = []
    for i, line in enumerate(merged):
        result.append(line["text"])
        if i < len(merged) - 1:
            gap   = merged[i + 1]["y"] - line["y"]
            avg_h = (line["h"] + merged[i + 1]["h"]) / 2
            if gap > avg_h * 1.8:
                result.append("")
    return "\n".join(result)


def post_process_text(text: str) -> str:
    """英文连字符修复 + 中文段落合并 + 压缩空行"""
    text = re.sub(r'([a-zA-Z])-\n([a-zA-Z])', r'\1\2', text)
    lines, merged, i = text.split('\n'), [], 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            merged.append('')
            i += 1
            continue
        zh        = len(re.findall(r'[\u4e00-\u9fff]', line))
        is_zh     = zh > len(line) * 0.2
        next_line = lines[i + 1] if i + 1 < len(lines) else ''
        nz        = len(re.findall(r'[\u4e00-\u9fff]', next_line))
        next_zh   = nz > len(next_line) * 0.2
        ends_sent = bool(re.search(r'[。！？.!?…"」』）\]）]\s*$', line))
        if is_zh and next_zh and not ends_sent and next_line.strip():
            merged.append(line + next_line.strip())
            i += 2
            continue
        merged.append(line)
        i += 1
    text = '\n'.join(merged)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return '\n'.join(l.rstrip() for l in text.split('\n')).strip()


_NOISE_RE = [
    re.compile(r'^\s*\d{1,4}\s*$'),
    re.compile(r'^\s*[-=_*·]{4,}\s*$'),
    re.compile(r'[\ufffd\u25a1]{3,}'),
    re.compile(r'^\s*[A-Za-z]{1,3}\s*$'),
]


def filter_noise(text: str) -> str:
    return '\n'.join(l for l in text.split('\n')
                     if not any(p.search(l.strip()) for p in _NOISE_RE))


# ── OCR 引擎（懒加载，仅在需要时初始化）──────────────────────
_ocr_engine = None


def _get_ocr_engine():
    """获取 OCR 引擎（自动检测 GPU/CPU）"""
    global _ocr_engine
    if _ocr_engine is not None:
        return _ocr_engine
    try:
        from paddleocr import PaddleOCR
        import paddle
        device = "gpu" if paddle.device.is_compiled_with_cuda() else "cpu"
        _ocr_engine = PaddleOCR(use_textline_orientation=True, lang="ch", device=device)
        print(f"✅ OCR 引擎初始化完成（{device.upper()}）")
        return _ocr_engine
    except ImportError:
        print("⚠️  paddleocr 未安装，OCR 功能不可用")
        return None
    except Exception as e:
        print(f"⚠️  OCR 引擎初始化失败: {e}")
        return None


def _run_ocr_on_page(page) -> str:
    """对单页图像运行 OCR，返回文字字符串"""
    import fitz
    import numpy as np
    from PIL import Image

    ocr = _get_ocr_engine()
    if ocr is None:
        return ""

    try:
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        arr = np.array(img)

        results = list(ocr.predict(arr))
        lines   = []
        for result in results:
            if result is None:
                continue
            try:
                for text, score in zip(result["rec_texts"], result["rec_scores"]):
                    if text and float(score) >= 0.65:
                        lines.append(text.strip())
            except (KeyError, TypeError):
                pass
        return "\n".join(lines)
    except Exception as e:
        print(f"OCR 出错: {e}")
        return ""


def process_page_to_text(page) -> tuple[str, str]:
    """
    处理单页，返回 (文字内容, 模式)。
    v5 核心逻辑：text 提取后验证输出质量，不足则降级到 OCR。
    """
    # 1. 尝试文字提取
    if is_text_page(page):
        raw  = extract_text_page(page)
        text = post_process_text(filter_noise(raw))
        # ★ v5 关键修复：验证输出质量，不足则降级
        if len(text.strip()) >= TEXT_EXTRACT_MIN_CHARS:
            return text, "text"

    # 2. 降级：OCR（需要 paddleocr）
    raw  = _run_ocr_on_page(page)
    text = post_process_text(filter_noise(raw))
    return text, "ocr"


def pdf_to_txt(pdf_path: Path) -> tuple[str, str, int]:
    """PDF → TXT，返回 (全文含header, 标题猜测, 页数)"""
    import fitz
    doc   = fitz.open(str(pdf_path))
    total = len(doc)
    pages = []
    title = ""
    counter = Counter()

    for num in range(total):
        text, mode = process_page_to_text(doc[num])
        counter[mode] += 1

        # 不从正文猜标题，保留 pdf_path.stem（原始文件名）作为书名

        pages.append(f"--- 第 {num+1} 页 / Page {num+1} [{mode}] ---\n{text}")

    doc.close()

    mode_summary = " / ".join(
        f"{k} {v} 页" for k, v in counter.items() if v > 0
    )
    print(f"  📊 {mode_summary}")
    if counter.get("ocr", 0) == total:
        print("  ℹ️  全部 OCR 提取（PDF 可能是扫描版或自定义字体编码）")

    full_text = "\n\n".join(pages)
    stem      = pdf_path.stem
    header    = (
        f"文件名：{stem}.txt\n"
        f"原始文件：{pdf_path.name}\n"
        f"转换时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{'='*60}\n\n"
    )
    return header + full_text, title, total



def _sanitize_filename(name: str, max_len: int = 60) -> str:
    """去除文件名中 Windows/Linux 均不合法的字符，限制长度"""
    name = re.sub(r'[\\/*?:"<>|\r\n\t]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:max_len]

def txt_read(txt_path: Path) -> tuple[str, str]:
    """
    读取已有 TXT，返回 (内容, 原始书名)。
    优先从 TXT 头部的 "原始文件：xxx.pdf" 行提取书名，
    避免把 "转换时间：..." 等元信息误当做书名。
    """
    content = txt_path.read_text(encoding='utf-8', errors='ignore')
    title   = ""
    for line in content.split('\n')[:10]:
        # 优先：从 "原始文件：xxx.pdf" 提取，去掉后缀和括号内容
        m = re.match(r'^原始文件：(.+\.pdf)$', line.strip())
        if m:
            raw = m.group(1)
            raw = re.sub(r'\s*\(z-library.*?\)', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'\.pdf$', '', raw).strip()
            if raw:
                title = raw
                break
    return content, title


# ============================================================
# 语料库构建（同步 v5 逻辑）
# ============================================================

class CONFIG:
    MIN_CHUNK_CHARS = 150
    MAX_CHUNK_CHARS = 6000
    POOR_OCR_AVG_LINE_LEN = 15

    SKIP_SECTION_TITLES = [
        "copyright", "版权", "版权信息", "isbn",
        "o'reilly", "oreilly", "safari在线", "safari books", "o'reilly media",
        "manning", "packt", "springer",
        "关于本书", "about this book", "who this book is for",
        "如何联系我们", "contact us",
        "本书赞誉", "业界评论",
        "致谢", "acknowledgment", "acknowledgements",
        "references", "bibliography", "参考文献", "参考书目",
        "further reading", "for further reading",
        "suggested reading", "additional reading",
        "index", "索引",
        "前言/preface", "summary", "摘要",
    ]

    NOISE_LINE_KEYWORDS = [
        "www.", "http://", "https://",
        "cambridge.org", "doi:", "lccn.loc",
        "all rights reserved", "printed in", "first published",
        "©", "侵权必究", "版权所有", "未经许可", "不得转载",
        "o'reilly media", "safari在线电子书",
        "isbn", "hardback", "paperback",
        "download at", "licensed to", "downloaded from",
    ]

    NOISE_LINE_PATTERNS = [
        r'^\s*[-=_*#~·]{4,}\s*$',
        r'^\s*\d{1,4}\s*$',
        r'^\s*[^\u4e00-\u9fffA-Za-z0-9]+\s*$',
        r'[\ufffd\u25a1\u25cb\u0000]{3,}',
        r'^\s*\.{4,}\s*\d*\s*$',
        r'^---\s*第\s*\d+\s*页',
    ]

    OCR_FIXES = [
        (r'\r\n', '\n'), (r'\r', '\n'),
        (r'　', ' '),
        (r'[ \t]{3,}', '  '),
        (r'\n{4,}', '\n\n\n'),
    ]

    STEP_VERBS = {
        'add','apply','assign','average','calculate','check','choose',
        'combine','compute','conduct','consider','construct','convert',
        'count','create','define','determine','develop','divide','draw',
        'establish','estimate','evaluate','examine','execute','explore',
        'find','fit','follow','form','generate','get','give','group',
        'handle','identify','implement','initialize','insert','iterate',
        'label','list','load','make','map','measure','minimize','modify',
        'normalize','note','obtain','optimize','order','output','partition',
        'perform','pick','plot','predict','print','process','rank','read',
        'record','reduce','remove','repeat','replace','report','resample',
        'retain','return','run','sample','scale','select','set','shuffle',
        'simulate','solve','sort','specify','split','start','store','sum',
        'summarize','take','test','train','transform','try','update','use',
        'validate','verify','visualize','write',
        'how','what','when','where','why','which',
        'append','boost','classify','cluster','drop','extract',
        'filter','grow','impute','join','keep','merge',
        'prune','skip','stop','tune','weight',
    }

    TITLE_PATTERNS: list[tuple] = [
        (r'^\s*第\s*[一二三四五六七八九十百零\d]+\s*部分\s*[：:．.\s]*(.{0,40})$', 'part', 0),
        (r'^\s*第\s*[一二三四五六七八九十百零\d]+\s*章\s*[：:．.\s]*(.{0,40})$',   'chapter', 1),
        (r'^\s*第\s*[一二三四五六七八九十百零\d]+\s*节\s*[：:．.\s]*(.{0,40})$',   'section', 2),
        (r'^\s*[一二三四五六七八九十]+[、]\s*(.{2,25})$',                           'section', 2),
        (r'^\s*Part\s+'
         r'(I{1,3}|IV|VI{0,3}|IX|X{1,3}|XI{0,3}|XIV|XV|'
         r'One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d{1,2})'
         r'(?=\s*$|\s*[.:\-–—\s])'
         r'[.]?\s*(?:[:\-–—]\s*)?(.{0,80})?$', 'part', 0),
        (r'^\s*Chapter\s+'
         r'(\d{1,2}|I{1,3}|IV|VI{0,3}|IX|'
         r'One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|'
         r'Eleven|Twelve|Thirteen|Fourteen|Fifteen|'
         r'Sixteen|Seventeen|Eighteen|Nineteen|Twenty)'
         r'(?:\s*$|[.]\s+[A-Za-z\u4e00-\u9fff]|\s*[:\-–—]\s*[A-Za-z]'
         r'|\s+[A-Za-z\u4e00-\u9fff\(])'
         r'(.{0,78})?$', 'chapter', 1),
        (r'^\s*CHAPTER\s+'
         r'(\d{1,2}|I{1,3}|IV|VI{0,3}|IX|'
         r'ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|'
         r'ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|'
         r'SIXTEEN|SEVENTEEN|EIGHTEEN|NINETEEN|TWENTY)'
         r'(?:\s*$|[.]\s+[A-Za-z\u4e00-\u9fff]|\s*[:\-–—]\s*[A-Za-z]'
         r'|\s+[A-Za-z\u4e00-\u9fff\(])'
         r'(.{0,78})?$', 'chapter', 1),
        (r'^\s*C\s*H\s*A\s*P\s*T\s*E\s*R\s+(\d{1,2}|I{1,3}|IV|VI{0,3}|IX)\s*(.{0,60})?$',
         'chapter', 1),
        (r'^\s*Section\s+\d+[\.\d]*\s+[A-Z\u4e00-\u9fff].{0,55}$', 'section', 2),
        (r'^\s*Appendix\s+[A-Z\d][.]?\s*[:\-–—]?\s*.{0,60}$',       'appendix', 3),
        (r'^\s*(\d{1,2}\.\d{1,3})\s+([A-Z\u4e00-\u9fff].{3,80})$',          'section',    2),
        (r'^\s*(\d{1,2}\.\d{1,3}\.\d{1,3})\s+([A-Z\u4e00-\u9fff].{3,60})$', 'subsection', 3),
        (r'^\s*(\d{1,2})\s+([A-Z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff ,\(\)\-]{8,70})$',
         'chapter', 1),
        (r'^\s*(\d{1,2})[.]\s+([A-Z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff ,\(\)\-]{9,70}[^.:\n])$',
         'chapter', 1),
    ]


def _normalize_part(text: str) -> str:
    def fix_roman(tok: str) -> str:
        c = tok.replace('l', 'I').replace('1', 'I')
        if re.fullmatch(r'M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', c, re.I) and c:
            return c
        return tok
    m = re.match(r'^(Part|PART)(\d+)(.*)', text)
    if m:
        return m.group(1) + ' ' + m.group(2) + m.group(3)
    m = re.match(r'^(Part|PART)\s+([IVXLivxl1]{1,6})(.*)', text, re.I)
    if m:
        return m.group(1) + ' ' + fix_roman(m.group(2)) + m.group(3)
    return text


def _normalize_section_num(text: str) -> str:
    return re.sub(r'^(\d{1,2}\.\d{1,3})([A-Z\u4e00-\u9fff])', r'\1 \2', text)


def _is_body_sentence(line: str) -> bool:
    s = line.strip()
    if len(s) > 90 or (s and s[0].islower()):
        return True
    if re.search(r'[.,:;]\s+[a-z]', s):
        return True
    if re.match(r'^(Chapter|Part|Section)\s+[\d\.]+[.)]\s*', s, re.I):
        return True
    return False


def _is_list_item(text: str, cfg=CONFIG) -> bool:
    t = text.strip()
    if t.endswith('.') or t.endswith(':'):
        return True
    m = re.match(r'^\s*\d{1,2}[.]\s+([A-Za-z]+)', t)
    if m and m.group(1).lower() in cfg.STEP_VERBS:
        return True
    if re.search(r'[A-Z][a-z]+,[a-z]', t):
        return True
    return False


def _is_standalone_heading(line: str) -> bool:
    s = line.strip()
    return bool(
        re.match(r'^\s*(Chapter|CHAPTER|C\s*H\s*A\s*P\s*T\s*E\s*R)\s+\d{1,2}\s*$', s, re.I)
        or re.match(r'^\s*(Chapter|CHAPTER)\s*$', s, re.I)
        or re.match(r'^\s*(Part|PART)\s+(\d{1,2}|I{1,3}|IV|VI{0,3}|IX|X{1,2})\s*$', s, re.I)
        or re.match(r'^\s*(\d{1,2})\s*$', s)
    )


def _is_continuation(line: str, allow_digit: bool = False) -> bool:
    s = line.strip()
    if not s or len(s) > 70:
        return False
    if len(s) > 15 and ' ' not in s and re.search(r'[a-z]{5,}', s):
        return False
    if re.search(r'\.\s+[a-z]', s) or re.search(r'[,;]\s+[a-z]{3,}', s):
        return False
    if allow_digit and re.match(r'^\d{1,2}[.]', s):
        return True
    return bool(
        re.match(r'^[A-Z\u4e00-\u9fff]', s)
        and not re.match(r'^\d', s)
        and 3 <= len(s) <= 70
    )


def merge_multiline_titles(lines: list[str]) -> list[str]:
    """合并被 OCR 断行的多行标题"""
    result, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not _is_standalone_heading(line):
            result.append(line)
            i += 1
            continue

        base            = line.strip()
        is_bare_chapter = bool(re.match(r'^\s*(Chapter|CHAPTER)\s*$', base, re.I))
        is_bare_digit   = bool(re.match(r'^\s*\d{1,2}\s*$', base))
        max_cont        = 5 if is_bare_chapter else (3 if is_bare_digit else 2)

        j = i + 1
        while j < len(lines) and (j - i) <= max_cont:
            ns = lines[j].strip()
            if not ns or len(base) + len(ns) + 1 > 90:
                break
            if _is_continuation(lines[j], allow_digit=is_bare_chapter):
                base += ' ' + ns
                j    += 1
            else:
                break

        if is_bare_digit and j == i + 1:
            result.append(line)
            i += 1
            continue

        result.append(base)
        i = j

    return result


def build_header_counter(lines: list[str]) -> Counter:
    counter: Counter = Counter()
    for line in lines:
        l = line.strip()
        if not l:
            continue
        norm = re.sub(r'\s+', ' ', l)
        if (5 <= len(norm) <= 100
                and re.search(r'[A-Za-z\u4e00-\u9fff]', norm)
                and not re.match(r'^[\d\s\(\)\[\]\{\}.,;:+\-=*/\\^<>|~]+$', norm)):
            counter[norm] += 1
    return counter


def section_prefix(title: str) -> Optional[str]:
    m = re.match(r'^\s*(\d{1,2}\.\d{1,3})', title)
    if m:
        return m.group(1)
    m = re.match(r'^\s*(?:Chapter|CHAPTER)\s+(\d{1,2})', title, re.I)
    if m:
        return f'ch_{m.group(1)}'
    m = re.match(r'^\s*Part\s+(\S+)', title, re.I)
    if m:
        return f'part_{m.group(1).upper()}'
    return None


def detect_title(
    line: str,
    header_counter: Optional[Counter] = None,
    cfg=CONFIG,
) -> Optional[tuple]:
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return None
    if header_counter:
        norm = re.sub(r'\s+', ' ', stripped)
        if header_counter.get(norm, 0) >= 2:
            return None
    if _is_body_sentence(stripped):
        return None

    normalized = _normalize_section_num(_normalize_part(stripped))

    for pattern, level, priority in cfg.TITLE_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            if level == 'chapter' and re.match(r'^\d{1,2}\.', normalized):
                if _is_list_item(normalized, cfg):
                    return None
            return (level, priority, normalized)

    return None


def is_noise_line(line: str, cfg=CONFIG) -> bool:
    low = line.lower().strip()
    if not low:
        return False
    for kw in cfg.NOISE_LINE_KEYWORDS:
        if kw in low:
            return True
    for pat in cfg.NOISE_LINE_PATTERNS:
        if re.search(pat, line):
            return True
    return False


def clean_text(text: str, cfg=CONFIG) -> str:
    for pat, repl in cfg.OCR_FIXES:
        text = re.sub(pat, repl, text)
    kept = [l.rstrip() for l in text.split('\n') if not is_noise_line(l, cfg)]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(kept)).strip()


def detect_language(text: str) -> str:
    zh = len(re.findall(r'[\u4e00-\u9fff]', text))
    en = len(re.findall(r'[A-Za-z]', text))
    return 'zh' if zh > en * 0.3 else 'en'


def build_corpus_from_txt(
    txt_content: str,
    book_id: str,
    book_name: str,
    source_file: str,
    cfg=CONFIG,
) -> list[dict]:
    """将 TXT 内容切分为标准化语料库记录（同步 v5 完整逻辑）"""

    lines_all = txt_content.split('\n')
    body      = '\n'.join(lines_all[5:]) if len(lines_all) > 5 else txt_content
    lang      = detect_language(body[:5000])

    # OCR 质量检测
    body_lines    = [l for l in body.split('\n') if l.strip()]
    avg_line_len  = (sum(len(l) for l in body_lines) / len(body_lines)) if body_lines else 0
    is_poor_ocr   = avg_line_len < cfg.POOR_OCR_AVG_LINE_LEN

    lines = merge_multiline_titles(body.split('\n'))

    if is_poor_ocr:
        # 按页切分（OCR 质量差时，每页为一段）
        chunks = []
        cur_lines, page_num = [], 1
        for line in lines:
            if re.match(r'^---\s*第\s*(\d+)\s*页', line):
                if cur_lines:
                    chunks.append({'title': f'第{page_num}页', 'level': 'page',
                                   'text': '\n'.join(cur_lines)})
                    cur_lines = []
                m = re.match(r'^---\s*第\s*(\d+)\s*页', line)
                page_num = int(m.group(1)) if m else page_num + 1
            else:
                cur_lines.append(line)
        if cur_lines:
            chunks.append({'title': f'第{page_num}页', 'level': 'page',
                           'text': '\n'.join(cur_lines)})
    else:
        # 按章节标题切分（含页眉过滤）
        header_counter = build_header_counter(lines)
        chunks     = []
        cur_lines  = []
        cur_title  = '导言'
        cur_level  = 'intro'

        def _flush():
            if cur_lines:
                chunks.append({'title': cur_title, 'level': cur_level,
                               'text': '\n'.join(cur_lines)})

        for line in lines:
            result = detect_title(line, header_counter, cfg)
            if result:
                level, _priority, title = result
                tl = title.lower().strip()
                if any(kw in tl for kw in cfg.SKIP_SECTION_TITLES):
                    cur_lines.append(line)
                    continue
                _flush()
                cur_lines = []
                cur_title = title
                cur_level = level
            else:
                cur_lines.append(line)
        _flush()

    if not chunks:
        chunks = [{'title': book_name, 'level': 'book', 'text': body}]

    # 编号前缀去重（合并同节碎片）
    merged_chunks: list[dict] = []
    for chunk in chunks:
        prefix      = section_prefix(chunk['title'])
        last_prefix = section_prefix(merged_chunks[-1]['title']) if merged_chunks else None
        if prefix and prefix == last_prefix and merged_chunks[-1]['level'] == chunk['level']:
            merged_chunks[-1]['text'] += '\n\n' + chunk['text']
        else:
            merged_chunks.append(chunk)

    # 清洗 + 构建记录 + 超长拆分
    records: list[dict] = []
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for chunk in merged_chunks:
        text = clean_text(chunk['text'], cfg)
        if len(text) < cfg.MIN_CHUNK_CHARS:
            continue

        def _make_rec(t: str) -> dict:
            return {
                'book_id':       book_id,
                'book_title':    book_name,
                'language':      lang,
                'source_file':   source_file,
                'chapter_title': chunk['title'],
                'chapter_level': chunk['level'],
                'chunk_index':   0,
                'total_chunks':  0,
                'text':          t,
                'char_count':    len(t),
                'created_at':    ts,
            }

        if len(text) <= cfg.MAX_CHUNK_CHARS:
            records.append(_make_rec(text))
        else:
            parts, buf = re.split(r'\n{2,}', text), []
            for part in parts:
                buf.append(part)
                if sum(len(p) for p in buf) >= cfg.MAX_CHUNK_CHARS // 2:
                    records.append(_make_rec('\n\n'.join(buf)))
                    buf = []
            if buf:
                records.append(_make_rec('\n\n'.join(buf)))

    total = len(records)
    for idx, rec in enumerate(records, 1):
        rec['chunk_index']  = idx
        rec['total_chunks'] = total

    return records


# ============================================================
# API 路由
# ============================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传 PDF 或 TXT 文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '文件名为空'}), 400

    book_id   = str(uuid.uuid4())[:8]
    ext       = Path(file.filename).suffix.lower()
    safe_name = f"{book_id}_{file.filename}"
    save_path = UPLOAD_DIR / safe_name
    file.save(str(save_path))

    file_size = save_path.stat().st_size
    pages     = 0

    if ext == '.pdf':
        try:
            import fitz
            doc   = fitz.open(str(save_path))
            pages = len(doc)
            doc.close()
        except Exception:
            pages = 0
    elif ext == '.txt':
        content = save_path.read_text(encoding='utf-8', errors='ignore')
        pages   = content.count('\n--- 第') or (len(content) // 3000) or 1

    book_info = {
        'id':          book_id,
        'name':        Path(file.filename).stem,
        'file':        file.filename,
        'size':        f"{file_size / 1024 / 1024:.1f} MB",
        'pages':       pages,
        'ext':         ext,
        'upload_path': str(save_path),
        'status':      'uploaded',
    }
    books_db[book_id] = book_info
    return jsonify(book_info)


@app.route('/api/books', methods=['GET'])
def list_books():
    return jsonify(list(books_db.values()))


@app.route('/api/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    if book_id in books_db:
        book = books_db.pop(book_id)
        for p in [book.get('upload_path'), book.get('txt_path'),
                  book.get('corpus_path'), book.get('graph_path')]:
            if p and Path(p).exists():
                Path(p).unlink()
    return jsonify({'ok': True})


@app.route('/api/preview/<book_id>', methods=['GET'])
def preview_book(book_id):
    """获取书籍原文预览（前2000字符左右）"""
    book = books_db.get(book_id)
    if not book:
        return jsonify({'error': '书籍不存在'}), 404

    upload_path = Path(book['upload_path'])
    preview_text = ""
    total_chars = 0

    try:
        if book['ext'] == '.txt':
            content = upload_path.read_text(encoding='utf-8', errors='ignore')
            total_chars = len(content)
            # 跳过文件头（元信息行）
            lines = content.split('\n')
            body_start = 0
            for i, line in enumerate(lines[:10]):
                if line.startswith('=' * 10):
                    body_start = i + 1
                    break
            body = '\n'.join(lines[body_start:])
            # 去掉页面分隔符行
            clean_lines = [l for l in body.split('\n')
                          if not re.match(r'^---\s*第\s*\d+\s*页', l)
                          and l.strip()]
            preview_text = '\n'.join(clean_lines[:80])

        elif book['ext'] == '.pdf':
            import fitz
            doc = fitz.open(str(upload_path))
            pages_text = []
            for i in range(min(5, len(doc))):
                page = doc[i]
                text = page.get_text("text").strip()
                if text:
                    pages_text.append(text)
            doc.close()
            preview_text = '\n\n'.join(pages_text)[:3000]
            total_chars = len(preview_text)

        # 检测语言
        zh = len(re.findall(r'[\u4e00-\u9fff]', preview_text[:2000]))
        en = len(re.findall(r'[A-Za-z]', preview_text[:2000]))
        lang = 'zh' if zh > en * 0.3 else 'en'

        return jsonify({
            'preview': preview_text[:3000],
            'total_chars': total_chars or len(preview_text),
            'language': lang,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/process/txt/<book_id>', methods=['POST'])
def process_to_txt(book_id):
    """任务1：PDF/TXT → 标准化 TXT"""
    book = books_db.get(book_id)
    if not book:
        return jsonify({'error': '书籍不存在'}), 404

    upload_path = Path(book['upload_path'])
    try:
        if book['ext'] == '.pdf':
            full_text, _title, pages = pdf_to_txt(upload_path)
            book['pages'] = pages
        else:
            full_text, _title = txt_read(upload_path)
            # 不用猜测的标题覆盖 book['name']，保留用户上传时的原始文件名

        safe_name = _sanitize_filename(book['name'])
        txt_path  = TXT_DIR / f"{book_id}_{safe_name}.txt"
        txt_path.write_text(full_text, encoding='utf-8')
        book['txt_path']    = str(txt_path)
        book['txt_content'] = full_text
        book['status']      = 'txt_ready'

        preview = '\n'.join(full_text.split('\n')[:50])
        return jsonify({
            'ok':          True,
            'book':        book,
            'preview':     preview,
            'total_chars': len(full_text),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/process/corpus/<book_id>', methods=['POST'])
def process_corpus(book_id):
    """任务2~5：切分 → 打标签 → 清洗 → 语料库"""
    book = books_db.get(book_id)
    if not book:
        return jsonify({'error': '书籍不存在'}), 404

    try:
        if 'txt_content' not in book:
            upload_path = Path(book['upload_path'])
            if book['ext'] == '.pdf':
                full_text, _title, pages = pdf_to_txt(upload_path)
                book['pages'] = pages
            else:
                full_text, _title = txt_read(upload_path)
                # 不覆盖 book['name']，保留原始文件名
            safe_name = _sanitize_filename(book['name'])
            txt_path  = TXT_DIR / f"{book_id}_{safe_name}.txt"
            txt_path.write_text(full_text, encoding='utf-8')
            book['txt_path']    = str(txt_path)
            book['txt_content'] = full_text

        records = build_corpus_from_txt(
            book['txt_content'],
            book_id,
            book['name'],
            book['file'],
        )

        corpus_path = CORPUS_DIR / f"{book_id}_corpus.json"
        with open(corpus_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        book['corpus_path'] = str(corpus_path)
        book['corpus']      = records
        book['status']      = 'corpus_ready'

        return jsonify({
            'ok':     True,
            'book':   book,
            'corpus': records,
            'stats': {
                'total_chunks': len(records),
                'total_chars':  sum(r['char_count'] for r in records),
                'language':     records[0]['language'] if records else 'unknown',
                'levels':       dict(Counter(r['chapter_level'] for r in records)),
            },
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/corpus/<book_id>', methods=['GET'])
def get_corpus(book_id):
    book = books_db.get(book_id)
    if not book or 'corpus' not in book:
        return jsonify({'error': '语料库尚未生成'}), 404
    return jsonify({'corpus': book['corpus']})


@app.route('/api/corpus/<book_id>/edit', methods=['POST'])
def edit_corpus_chunk(book_id):
    book = books_db.get(book_id)
    if not book or 'corpus' not in book:
        return jsonify({'error': '语料库尚未生成'}), 404

    data        = request.json or {}
    chunk_index = data.get('chunk_index')
    new_text    = data.get('text', '')

    for rec in book['corpus']:
        if rec['chunk_index'] == chunk_index:
            rec['text']       = new_text
            rec['char_count'] = len(new_text)
            rec['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break

    with open(book['corpus_path'], 'w', encoding='utf-8') as f:
        json.dump(book['corpus'], f, ensure_ascii=False, indent=2)

    return jsonify({'ok': True})


@app.route('/api/process/graph/<book_id>', methods=['POST'])
def process_graph(book_id):
    book = books_db.get(book_id)
    if not book or 'corpus' not in book:
        return jsonify({'error': '请先生成语料库'}), 404

    try:
        api_key    = (request.json or {}).get('api_key', '')
        graph_data = (call_deepseek_extract(book['corpus'], api_key)
                      if api_key else
                      simple_keyword_extract(book['corpus'], book['name']))

        graph_path = GRAPH_DIR / f"{book_id}_graph.json"
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        book['graph_path'] = str(graph_path)
        book['graph']      = graph_data
        book['status']     = 'graph_ready'

        return jsonify({'ok': True, 'graph': graph_data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/graph/<book_id>', methods=['GET'])
def get_graph(book_id):
    book = books_db.get(book_id)
    if not book or 'graph' not in book:
        return jsonify({'error': '图谱尚未生成'}), 404
    return jsonify({'graph': book['graph']})


@app.route('/api/process/global-graph', methods=['POST'])
def process_global_graph():
    data      = request.json or {}
    book_ids  = data.get('book_ids', [])
    seen, all_entities, all_relations = {}, [], []

    for bid in book_ids:
        book = books_db.get(bid)
        if not book or 'graph' not in book:
            continue
        for e in book['graph'].get('entities', []):
            key = e['name'].lower().strip()
            if key not in seen:
                seen[key] = e
                all_entities.append(e)
        all_relations.extend(book['graph'].get('relations', []))

    global_graph = {
        'entities':   all_entities,
        'relations':  all_relations,
        'book_count': len(book_ids),
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    path = GRAPH_DIR / "global_graph.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(global_graph, f, ensure_ascii=False, indent=2)

    return jsonify({'ok': True, 'graph': global_graph})


@app.route('/api/download/<book_id>/<dtype>', methods=['GET'])
def download_file(book_id, dtype):
    book = books_db.get(book_id)
    if not book:
        return jsonify({'error': '书籍不存在'}), 404
    if dtype == 'corpus' and 'corpus_path' in book:
        return send_file(book['corpus_path'], as_attachment=True)
    if dtype == 'graph' and 'graph_path' in book:
        return send_file(book['graph_path'], as_attachment=True)
    return jsonify({'error': '文件不存在'}), 404


# ============================================================
# DeepSeek API
# ============================================================

def call_deepseek_extract(corpus: list, api_key: str) -> dict:
    import urllib.request

    sample = ''.join(
        f"\n\n## {r['chapter_title']}\n{r['text'][:800]}"
        for r in corpus[:5]
    )
    prompt = f"""请从以下教材文本中提取知识图谱，返回 JSON 格式：
{{
  "entities": [
    {{"id": "e1", "name": "实体名", "type": "concept/algorithm/task/process", "definition": "简短定义"}}
  ],
  "relations": [
    {{"source": "e1", "target": "e2", "relation": "关系类型（如：包含、依赖、应用于）"}}
  ]
}}

要求：
1. 提取 10-20 个核心实体
2. 实体类型：concept（概念）、algorithm（算法）、task（任务）、process（流程）
3. 关系类型：包含、依赖、应用于、前置条件、衍生
4. 只返回 JSON，不要其他文字

文本内容：
{sample[:3000]}
"""
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000,
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result  = json.loads(resp.read().decode('utf-8'))
    content = result['choices'][0]['message']['content'].strip()
    if content.startswith('```'):
        content = re.sub(r'^```json?\s*', '', content)
        content = re.sub(r'```\s*$',      '', content)
    return json.loads(content)


def simple_keyword_extract(corpus: list, book_name: str) -> dict:
    entities, seen, eid = [], set(), 0

    for rec in corpus:
        title = rec['chapter_title']
        if title not in seen and title not in ('导言', '第1页', 'book'):
            seen.add(title)
            eid += 1
            entities.append({'id': f'e{eid}', 'name': title, 'type': 'chapter',
                             'definition': f'来自《{book_name}》，含 {rec["char_count"]} 字符'})

    all_text = ' '.join(r['text'] for r in corpus)
    stopwords = {'进行', '通过', '可以', '使用', '其中', '以及', '或者', '这个',
                 '一个', '我们', '它们', '这些', '那些', '已经', '应该', '需要'}

    zh_freq = Counter(re.findall(r'[\u4e00-\u9fff]{2,6}', all_text))
    for word, count in zh_freq.most_common(30):
        if word not in seen and count >= 3 and word not in stopwords:
            seen.add(word)
            eid += 1
            entities.append({'id': f'e{eid}', 'name': word, 'type': 'concept',
                             'definition': f'在文本中出现 {count} 次'})
            if len(entities) >= 20:
                break

    en_freq = Counter(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b', all_text))
    for phrase, count in en_freq.most_common(15):
        if phrase not in seen and count >= 2:
            seen.add(phrase)
            eid += 1
            entities.append({'id': f'e{eid}', 'name': phrase, 'type': 'concept',
                             'definition': f'在文本中出现 {count} 次'})
            if len(entities) >= 25:
                break

    chapter_ents = [e for e in entities if e['type'] == 'chapter']
    concept_ents = [e for e in entities if e['type'] == 'concept']
    relations    = []
    for ce in chapter_ents[:8]:
        for rec in corpus:
            if rec['chapter_title'] == ce['name']:
                for ke in concept_ents[:10]:
                    if ke['name'] in rec['text']:
                        relations.append({'source': ce['id'], 'target': ke['id'], 'relation': '涉及'})
                break

    return {'entities': entities[:25], 'relations': relations[:40]}


# ============================================================
# 启动
# ============================================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  知识图谱平台 API 服务")
    print("  http://localhost:5000")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
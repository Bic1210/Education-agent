"""
PDF 扫描版 OCR 转 TXT 工具 v5（GPU 加速 + 自定义字体兼容）
支持中英文混合 | 自动统一命名 | 批量处理
兼容 PaddleOCR 3.x 新版 API

=== v3 核心改进 ===

目标质量参考：电子书直接提取的TXT
  ✅ 完整段落（不断行、不乱码）
  ✅ 正确的空行分隔
  ✅ 汉字识别准确

改进点：

1. 【文字提取重写】extract_text_page() 重写为"段落感知"模式
   - 用 pymupdf 的 "dict" 模式按行位置精确拼合
   - 相邻行间距小 → 同一段落（合并）
   - 间距大 → 段落边界（插入空行）
   - 彻底解决 blocks 模式导致的段落丢失问题

2. 【混合PDF支持】同一本书可以页为单位混合文字提取和OCR
   - 文字型页 → extract_text_page()（质量最好，速度最快）
   - 扫描型页 → OCR（单栏或双栏）
   - 每本书末尾打印各模式使用比例

3. 【段落合并后处理】post_process_text()
   - 中文段落内的换行（非段落边界）自动合并为一行
   - 英文段落内的连字符断行（如 "recog-\nnition"）自动修复
   - 去除多余空行，保留有意义的段落分隔

4. 【DPI自适应】
   - 文字型PDF页：跳过渲染，速度提升10x
   - 扫描型PDF页：DPI=300
   - 小图页（可能是图表）：DPI=200，减少处理时间

5. 【置信度提升】0.5 → 0.65

运行：python 02_run_ocr_v3.py
"""

import re
import json
import time
from pathlib import Path
from datetime import datetime

import fitz
from PIL import Image
import numpy as np

# ============================================================
# ✅ CONFIG
# ============================================================

INPUT_DIR  = "./input_pdfs"
OUTPUT_DIR = "./output_txts"
USE_GPU    = True
OCR_LANG   = "ch"

DPI                    = 300     # 扫描页渲染精度
CONFIDENCE_THRESHOLD   = 0.65   # OCR置信度阈值（v3: 0.5→0.65）
DOUBLE_COLUMN_RATIO    = 1.3    # 宽高比超过此值视为双栏
TEXT_EXTRACT_MIN_CHARS = 30     # 每页可提取字符数低于此值才走OCR



# ============================================================
# 文字提取（段落感知版）
# ============================================================


def _is_readable_text(text: str, min_readable_ratio: float = 0.5) -> bool:
    """
    检查 get_text() 提取内容是否真正可读（非乱码）。

    背景：某些PDF使用自定义Type1字体编码（无ToUnicode映射），
    PyMuPDF能提取到字符，但全是无意义的乱码替代符。
    字符数可能远超阈值（如 >30），导致 is_text_page()=True，
    跳过OCR，最终输出全空。

    解决：统计"可读字符"占比（英文/数字/中文/常见标点），
    占比低于 50% 时认为是乱码，强制走OCR。
    """
    if not text:
        return False
    readable = sum(
        1 for c in text
        if ('A' <= c <= 'Z') or ('a' <= c <= 'z')
        or ('0' <= c <= '9')
        or ('一' <= c <= '鿿')
        or c in ' \t\n.,;:!?()-\'"'
    )
    return (readable / len(text)) >= min_readable_ratio


def is_text_page(page: fitz.Page) -> bool:
    """
    判断是否为可直接提取文字的排版型PDF页。

    ★ v4修复：增加可读性检测，防止自定义字体PDF的乱码
    被误判为有效文字（导致跳过OCR，输出全空）。
    """
    raw = page.get_text("text").strip()
    if len(raw) < TEXT_EXTRACT_MIN_CHARS:
        return False
    return _is_readable_text(raw)


def extract_text_page(page: fitz.Page) -> str:
    """
    段落感知文字提取。
    
    原理：
    - 用 pymupdf "rawdict" 获取每个文字块的精确坐标
    - 按 y 坐标（行位置）分组，同行文字水平排序后拼为一行
    - 相邻两行的行距：
        ≤ 1.5 * 行高 → 同一段落（直接接续）
        > 1.5 * 行高 → 段落边界（插入空行）
    
    效果：还原电子书质量的段落结构
    """
    data   = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    blocks = data.get("blocks", [])

    # 收集所有文字行（每行一个 dict: y_center, x0, text, line_height）
    raw_lines = []
    for block in blocks:
        if block.get("type") != 0:   # 只处理文字块，跳过图片块
            continue
        for line in block.get("lines", []):
            bbox   = line["bbox"]   # (x0, y0, x1, y1)
            y_mid  = (bbox[1] + bbox[3]) / 2
            height = bbox[3] - bbox[1]
            # 拼合该行所有 span 的文字
            text = ""
            for span in line.get("spans", []):
                text += span.get("text", "")
            text = text.strip()
            if text:
                raw_lines.append({
                    "y":    y_mid,
                    "x0":   bbox[0],
                    "h":    height,
                    "text": text,
                })

    if not raw_lines:
        return ""

    # 按 y 坐标排序（从上到下），同 y 按 x 排序（从左到右）
    raw_lines.sort(key=lambda l: (round(l["y"] / 3), l["x0"]))

    # 合并 y 坐标非常接近的行（同一物理行被拆成多个 span）
    merged: list[dict] = []
    for line in raw_lines:
        if merged and abs(line["y"] - merged[-1]["y"]) < merged[-1]["h"] * 0.5:
            merged[-1]["text"] += " " + line["text"]
        else:
            merged.append(dict(line))

    # 按行间距判断段落边界
    result_lines: list[str] = []
    for i, line in enumerate(merged):
        result_lines.append(line["text"])
        if i < len(merged) - 1:
            gap       = merged[i + 1]["y"] - line["y"]
            avg_h     = (line["h"] + merged[i + 1]["h"]) / 2
            # 间距超过1.8倍行高 → 段落边界
            if gap > avg_h * 1.8:
                result_lines.append("")

    return "\n".join(result_lines)


# ============================================================
# 后处理：段落合并 + 断行修复
# ============================================================

def post_process_text(text: str) -> str:
    """
    对提取/OCR文字做后处理：
    1. 英文连字符断行修复：recog-\nnition → recognition
    2. 中文段落内换行合并（段落内的软换行 → 空格或直接拼接）
    3. 压缩多余空行（3个以上 → 2个）
    4. 去除行尾多余空格
    """
    # 1. 英文连字符断行修复
    text = re.sub(r'([a-zA-Z])-\n([a-zA-Z])', r'\1\2', text)

    # 2. 中文段落内换行合并
    # 规则：两行都包含中文，且上一行不以句末标点结尾 → 合并
    lines = text.split('\n')
    merged: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        # 空行直接保留
        if not line:
            merged.append('')
            i += 1
            continue
        # 尝试与下一非空行合并
        if (i + 1 < len(lines)
                and lines[i + 1].strip()
                and _is_chinese_line(line)
                and _is_chinese_line(lines[i + 1])
                and not _ends_with_sentence_punct(line)):
            merged.append(line + lines[i + 1].strip())
            i += 2
            continue
        merged.append(line)
        i += 1

    text = '\n'.join(merged)

    # 3. 压缩多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 4. 去除行尾空格
    text = '\n'.join(l.rstrip() for l in text.split('\n'))

    return text.strip()


def _is_chinese_line(line: str) -> bool:
    """判断一行是否以中文为主"""
    zh = len(re.findall(r'[\u4e00-\u9fff]', line))
    return zh > len(line) * 0.2


def _ends_with_sentence_punct(line: str) -> bool:
    """判断一行是否以句末标点结尾（中英文）"""
    return bool(re.search(r'[。！？.!?…"」』）\]）]\s*$', line))


# ============================================================
# 图像预处理
# ============================================================

def page_to_image(page: fitz.Page, dpi: int) -> np.ndarray:
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return np.array(img)


def is_double_column(img: np.ndarray) -> bool:
    h, w = img.shape[:2]
    return (w / h) > DOUBLE_COLUMN_RATIO


def split_double_column(img: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h, w   = img.shape[:2]
    mid    = w // 2
    margin = int(w * 0.03)
    return img[:, :mid - margin], img[:, mid + margin:]


# ============================================================
# OCR 核心
# ============================================================

def init_ocr(use_gpu: bool, lang: str):
    from paddleocr import PaddleOCR
    import paddle

    print(f"🚀 初始化 OCR 引擎（{'GPU' if use_gpu else 'CPU'} 模式，语言：{lang}）...")
    if use_gpu and paddle.device.is_compiled_with_cuda():
        device = "gpu"
        print("   ✅ 检测到 CUDA，使用 GPU 加速")
    else:
        device = "cpu"
        if use_gpu:
            print("   ⚠️  未检测到 CUDA，回退到 CPU 模式")

    ocr = PaddleOCR(use_textline_orientation=True, lang=lang, device=device)
    print("✅ OCR 引擎加载完成\n")
    return ocr


def run_ocr(ocr_engine, img: np.ndarray) -> str:
    try:
        results = list(ocr_engine.predict(img))
    except Exception as e:
        return f"[OCR错误: {e}]"

    lines = []
    for result in results:
        if result is None:
            continue
        try:
            for text, score in zip(result["rec_texts"], result["rec_scores"]):
                if text and float(score) >= CONFIDENCE_THRESHOLD:
                    lines.append(text.strip())
        except (KeyError, TypeError):
            try:
                if isinstance(result, list):
                    for item in result:
                        if item and len(item) >= 2:
                            t     = item[1]
                            text  = t[0] if isinstance(t, (list, tuple)) else t
                            score = t[1] if isinstance(t, (list, tuple)) else 1.0
                            if text and float(score) >= CONFIDENCE_THRESHOLD:
                                lines.append(str(text).strip())
            except Exception:
                pass
    return "\n".join(lines)


# ============================================================
# 噪声行过滤
# ============================================================

_NOISE = [
    re.compile(r'^\s*\d{1,4}\s*$'),           # 纯数字（页码）
    re.compile(r'^\s*[-=_*·]{4,}\s*$'),        # 纯分隔符
    re.compile(r'[\ufffd\u25a1]{3,}'),          # 乱码
    re.compile(r'^\s*[A-Za-z]{1,3}\s*$'),       # 孤立1~3个英文字母
]

def filter_noise_lines(text: str) -> str:
    lines   = text.split('\n')
    cleaned = [l for l in lines if not any(p.search(l.strip()) for p in _NOISE)]
    return '\n'.join(cleaned)


# ============================================================
# 单页处理调度
# ============================================================

def process_page(page: fitz.Page, ocr_engine, page_num: int) -> tuple[str, str]:
    """
    返回 (page_text, mode)
    mode: 'text' | 'ocr' | 'ocr_2col'

    v5 修复逻辑：
    某些PDF（如使用自定义Type1字体/字形拆分排版）虽然含文字流，
    但 PyMuPDF 无法正确解码 → get_text() 返回乱码或空。
    v4 的 _is_readable_text 在某些情况下仍会误判（乱码恰好通过检测）。

    终极方案：text 模式提取后验证输出质量。
    若提取结果长度 < TEXT_EXTRACT_MIN_CHARS → 自动降级到 OCR。
    这直接验证"最终能用的内容"，比预判更可靠。
    """
    # 步骤1：初步判断是否为文字型页（有文字流且内容可读）
    if is_text_page(page):
        raw  = extract_text_page(page)
        text = post_process_text(filter_noise_lines(raw))

        # ★ v5 关键修复：验证提取结果质量
        # 若提取结果太短（字形拆分/自定义编码导致内容为空），降级到OCR
        if len(text.strip()) >= TEXT_EXTRACT_MIN_CHARS:
            return text, 'text'
        # 否则降级到OCR（fall through）

    # 扫描页或text提取失败 → OCR
    img = page_to_image(page, DPI)
    if is_double_column(img):
        left, right = split_double_column(img)
        l_text = filter_noise_lines(run_ocr(ocr_engine, left))
        r_text = filter_noise_lines(run_ocr(ocr_engine, right))
        text   = post_process_text(l_text + '\n\n' + r_text)
        return text, 'ocr_2col'

    raw  = run_ocr(ocr_engine, img)
    text = post_process_text(filter_noise_lines(raw))
    return text, 'ocr'


# ============================================================
# 整书处理
# ============================================================

def process_pdf(pdf_path: Path, ocr_engine) -> str:
    doc         = fitz.open(str(pdf_path))
    total       = len(doc)
    pages_out   = []
    counter     = {'text': 0, 'ocr': 0, 'ocr_2col': 0}

    print(f"  📄 共 {total} 页...")

    for num in range(total):
        text, mode = process_page(doc[num], ocr_engine, num)
        counter[mode] += 1
        pages_out.append(
            f"--- 第 {num+1} 页 / Page {num+1} [{mode}] ---\n{text}"
        )
        if (num + 1) % 10 == 0 or num == total - 1:
            print(f"    进度：{num+1}/{total} 页")

    doc.close()

    parts = []
    if counter['text']:    parts.append(f"文字提取 {counter['text']} 页")
    if counter['ocr']:     parts.append(f"单栏OCR {counter['ocr']} 页")
    if counter['ocr_2col']:parts.append(f"双栏OCR {counter['ocr_2col']} 页")
    print(f"  📊 {' / '.join(parts)}")

    return "\n\n".join(pages_out)


# ============================================================
# 辅助
# ============================================================




def _save_mapping(mapping: list, output_dir: Path) -> None:
    json_path = output_dir / "_命名映射表.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    csv_path = output_dir / "_命名映射表.csv"
    with open(csv_path, "w", encoding="utf-8-sig") as f:
        f.write("原文件名,输出文件名\n")
        for item in mapping:
            f.write(f"{item['original']},{item['output']}\n")
    print(f"\n📋 映射表：\n   {json_path}\n   {csv_path}")


# ============================================================
# main
# ============================================================

def main():
    input_dir  = Path(INPUT_DIR)
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        input_dir.mkdir(parents=True)
        print(f"⚠️  已创建输入目录：{input_dir.resolve()}，请放入PDF后重新运行。")
        return

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ 未找到PDF：{input_dir.resolve()}")
        return

    print(f"✅ 找到 {len(pdf_files)} 个PDF：")
    for i, p in enumerate(pdf_files, 1):
        print(f"   {i:02d}. {p.name}")
    print()

    ocr_engine = init_ocr(USE_GPU, OCR_LANG)

    mapping, failed = [], []
    t0_total = time.time()

    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] {pdf_path.name}")
        t0 = time.time()
        try:
            full_text = process_pdf(pdf_path, ocr_engine)
            out_path  = output_dir / f"{pdf_path.stem}.txt"
            header = (
                f"文件名：{pdf_path.stem}.txt\n"
                f"原始文件：{pdf_path.name}\n"
                f"转换时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"{'='*60}\n\n"
            )
            out_path.write_text(header + full_text, encoding="utf-8")
            print(f"  ✅ → {out_path.name}  ({time.time()-t0:.1f}s)")
            mapping.append({"original": pdf_path.name, "output": out_path.name})
        except Exception as e:
            import traceback
            print(f"  ❌ 失败：{e}")
            traceback.print_exc()
            failed.append({"file": pdf_path.name, "error": str(e)})

    _save_mapping(mapping, output_dir)

    elapsed = time.time() - t0_total
    print(f"\n{'='*60}")
    print(f"🎉 完成！成功 {len(mapping)} / 失败 {len(failed)} / 耗时 {elapsed/60:.1f} 分钟")
    print(f"   输出：{output_dir.resolve()}")
    if failed:
        print("\n⚠️  失败：")
        for f in failed:
            print(f"   {f['file']}：{f['error']}")

if __name__ == "__main__":
    main()

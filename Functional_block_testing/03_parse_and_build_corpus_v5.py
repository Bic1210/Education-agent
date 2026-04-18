"""
任务 2~5：文本解析 → 章节切分 → 打标签 → 清洗 → 输出标准化语料库
版本：v5 — 功能包化重构

架构：
    CONFIG              集中配置
    class PageFilter    任务2：页面过滤（目录/前置/缩略语）
    class TitleDetector 任务2：章节标题识别 + 多行合并
    class TextCleaner   任务4：文本清洗（噪声过滤 + OCR修复）
    class CorpusBuilder 任务2+3+5：切分 + 打标签 + 输出
    main()              串联以上，逐书处理

扩展示例：
    class ChineseTitleDetector(TitleDetector): ...   # 覆盖中文规则
    class PoorOCRBuilder(CorpusBuilder): ...         # 覆盖切分逻辑

修复历史：
  v2: Chapter识别、Part吞噬、罗马数字OCR容错
  v3: 目录连续页、header_counter、缩略语页、编号去重、正文引用误识别
  v4: O'Reilly多行标题合并、Part词边界、步骤动词黑名单
  v5: 类架构重构；修复纯数字章节标题(1/2/3)漏识别；
      新增逐词OCR降级策略（处理07类极差OCR书）；
      修复 "Section N.N) [ref]." 正文引用误识别

运行：python 03_parse_and_build_corpus_v5.py
"""

from __future__ import annotations

import re
import json
import csv
import time
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Optional

# ============================================================
# CONFIG
# ============================================================

class CONFIG:
    INPUT_DIR  = "./output_txts"
    OUTPUT_DIR = "./corpus"

    MIN_CHUNK_CHARS = 150
    MAX_CHUNK_CHARS = 6000

    # 页面过滤阈值
    TOC_THRESHOLD         = 0.55
    TOC_CONTINUATION_THR  = 0.35
    FRONTMATTER_THRESHOLD = 0.55
    ACRONYM_THRESHOLD     = 0.55

    # 逐词OCR降级：当一本书平均行长 < 此值时，整本书按页切分（不按标题切）
    # 07_the.txt 这类书每行只有1~3个单词，平均行长约5~8字符
    POOR_OCR_AVG_LINE_LEN = 15

    # 章节标题黑名单
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


# ============================================================
# PageFilter
# ============================================================

class PageFilter:
    """页面过滤：识别并跳过目录/前置/缩略语页"""

    def __init__(self, cfg: type = CONFIG):
        self.cfg = cfg

    def score_toc(self, lines: list[str]) -> float:
        non_empty = [l.strip() for l in lines if l.strip()]
        if not non_empty:
            return 0.0
        score = 0.0
        if any(re.match(r'^\s*(Contents|目录)\s*$', l, re.I) for l in non_empty):
            score += 0.5
        digit_ratio = sum(1 for l in non_empty
                          if re.match(r'^\s*\d{1,4}\s*$', l)) / len(non_empty)
        score += digit_ratio * 0.6
        avg_len = sum(len(l) for l in non_empty) / len(non_empty)
        score += 0.3 if avg_len < 20 else (0.1 if avg_len < 35 else 0)
        if any(re.search(r'\bpage\s+[ivxlcdm\d]+\b', l, re.I) for l in non_empty):
            score += 0.4
        return min(score, 1.0)

    def score_frontmatter(self, lines: list[str]) -> float:
        non_empty = [l.strip() for l in lines if l.strip()]
        if not non_empty:
            return 0.0
        score = 0.0
        text = ' '.join(non_empty).lower()
        if any(kw in text for kw in [
            'university press', 'cambridge', 'isbn', 'printed in',
            '©', 'all rights reserved', 'first published',
            'peachpit', 'new riders', 'pearson',
        ]):
            score += 0.5
        addr_hits = sum(1 for l in non_empty if re.search(
            r'\b(USA|UK|India|Singapore|Australia|London|New York|Cambridge)\b', l))
        if addr_hits >= 2:
            score += 0.3
        if (len(non_empty) <= 15
                and sum(len(l) for l in non_empty) / len(non_empty) < 25):
            score += 0.2
        return min(score, 1.0)

    def score_acronym(self, lines: list[str]) -> float:
        non_empty = [l.strip() for l in lines if l.strip()]
        if len(non_empty) < 10:
            return 0.0
        if sum(1 for l in non_empty if re.match(r'^\d{1,4}$', l)) > 2:
            return 0.0
        short_ratio = sum(1 for l in non_empty if 2 <= len(l) <= 8)  / len(non_empty)
        mid_ratio   = sum(1 for l in non_empty if 10 <= len(l) <= 70) / len(non_empty)
        if short_ratio > 0.20 and mid_ratio > 0.40:
            return min(short_ratio + mid_ratio * 0.5, 1.0)
        text = ' '.join(non_empty[:5]).lower()
        if any(kw in text for kw in [
            'acronym', 'abbreviation', 'notation', 'symbol', '缩略语', '符号', '缩写'
        ]):
            return 0.6
        return 0.0

    @staticmethod
    def split_pages(body: str) -> list[list[str]]:
        pages, current = [], []
        for line in body.split('\n'):
            if re.match(r'^---\s*第\s*\d+\s*页', line):
                if current:
                    pages.append(current)
                current = []
            else:
                current.append(line)
        if current:
            pages.append(current)
        return pages

    def filter(self, pages: list[list[str]]) -> tuple[list[str], dict]:
        """过滤并返回 (保留行列表, 跳过统计)"""
        cfg = self.cfg
        filtered:   list[str] = []
        stats = {'toc': 0, 'frontmatter': 0, 'acronym': 0}
        last_was_toc = False

        for page in pages:
            ts  = self.score_toc(page)
            fs  = self.score_frontmatter(page)
            acs = self.score_acronym(page)
            toc_thr = cfg.TOC_CONTINUATION_THR if last_was_toc else cfg.TOC_THRESHOLD

            if fs >= cfg.FRONTMATTER_THRESHOLD:
                stats['frontmatter'] += 1
                last_was_toc = False
                continue
            if acs >= cfg.ACRONYM_THRESHOLD:
                stats['acronym'] += 1
                last_was_toc = False
                continue
            if ts >= toc_thr:
                stats['toc'] += 1
                last_was_toc = True
                continue
            if ts == 0.0:
                last_was_toc = False

            filtered.extend(page)
            filtered.append('')

        return filtered, stats

    def debug_scores(self, txt_path: Path, n_pages: int = 30) -> None:
        content = txt_path.read_text(encoding='utf-8', errors='ignore')
        body    = '\n'.join(content.split('\n')[5:])
        pages   = self.split_pages(body)
        cfg     = self.cfg
        print(f'\n{"─"*72}\n🔍 PageFilter 分数：{txt_path.name}')
        print(f'  {"Page":>4} {"TOC":>5} {"Front":>5} {"Acronym":>7}  决定')
        print(f'{"─"*72}')
        last_was_toc = False
        for i, page in enumerate(pages[:n_pages]):
            ts, fs, acs = self.score_toc(page), self.score_frontmatter(page), self.score_acronym(page)
            thr = cfg.TOC_CONTINUATION_THR if last_was_toc else cfg.TOC_THRESHOLD
            decision = ('前置页' if fs >= cfg.FRONTMATTER_THRESHOLD else
                        '缩略语' if acs >= cfg.ACRONYM_THRESHOLD else
                        '目录页' if ts >= thr else '✅保留')
            print(f'  {i+1:4d}  {ts:5.2f}  {fs:5.2f}  {acs:7.2f}  {decision}')
            last_was_toc = (ts >= thr
                            and fs < cfg.FRONTMATTER_THRESHOLD
                            and acs < cfg.ACRONYM_THRESHOLD)
            if ts == 0.0:
                last_was_toc = False


# ============================================================
# TitleDetector
# ============================================================

class TitleDetector:
    """章节标题识别 + 多行标题合并"""

    PATTERNS: list[tuple[str, str, int]] = [
        # ── 中文 ─────────────────────────────────────────────
        (r'^\s*第\s*[一二三四五六七八九十百零\d]+\s*部分\s*[：:．.\s]*(.{0,40})$', 'part',       0),
        (r'^\s*第\s*[一二三四五六七八九十百零\d]+\s*章\s*[：:．.\s]*(.{0,40})$',   'chapter',    1),
        (r'^\s*第\s*[一二三四五六七八九十百零\d]+\s*节\s*[：:．.\s]*(.{0,40})$',   'section',    2),
        (r'^\s*[一二三四五六七八九十]+[、]\s*(.{2,25})$',                           'section',    2),
        # ── 英文 Part（词边界，防 "Partial" 误匹配）──────────
        (r'^\s*Part\s+'
         r'(I{1,3}|IV|VI{0,3}|IX|X{1,3}|XI{0,3}|XIV|XV|'
         r'One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d{1,2})'
         r'(?=\s*$|\s*[.:\-–—\s])'
         r'[.]?\s*(?:[:\-–—]\s*)?(.{0,80})?$',
         'part', 0),
        # ── 英文 Chapter ─────────────────────────────────────
        (r'^\s*Chapter\s+'
         r'(\d{1,2}|I{1,3}|IV|VI{0,3}|IX|'
         r'One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|'
         r'Eleven|Twelve|Thirteen|Fourteen|Fifteen|'
         r'Sixteen|Seventeen|Eighteen|Nineteen|Twenty)'
         r'(?:\s*$|[.]\s+[A-Za-z\u4e00-\u9fff]|\s*[:\-–—]\s*[A-Za-z]'
         r'|\s+[A-Za-z\u4e00-\u9fff\(])'
         r'(.{0,78})?$',
         'chapter', 1),
        (r'^\s*CHAPTER\s+'
         r'(\d{1,2}|I{1,3}|IV|VI{0,3}|IX|'
         r'ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|'
         r'ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|'
         r'SIXTEEN|SEVENTEEN|EIGHTEEN|NINETEEN|TWENTY)'
         r'(?:\s*$|[.]\s+[A-Za-z\u4e00-\u9fff]|\s*[:\-–—]\s*[A-Za-z]'
         r'|\s+[A-Za-z\u4e00-\u9fff\(])'
         r'(.{0,78})?$',
         'chapter', 1),
        (r'^\s*C\s*H\s*A\s*P\s*T\s*E\s*R\s+(\d{1,2}|I{1,3}|IV|VI{0,3}|IX)\s*(.{0,60})?$',
         'chapter', 1),
        # ── Section / Appendix ───────────────────────────────
        # ★ 必须排除 "Section N.N) [ref]." 这类正文引用（末尾有括号/点/引用数字）
        (r'^\s*Section\s+\d+[\.\d]*\s+[A-Z\u4e00-\u9fff].{0,55}$', 'section', 2),
        (r'^\s*Appendix\s+[A-Z\d][.]?\s*[:\-–—]?\s*.{0,60}$',       'appendix', 3),
        # ── 数字编号 N.N Title ───────────────────────────────
        (r'^\s*(\d{1,2}\.\d{1,3})\s+([A-Z\u4e00-\u9fff].{3,80})$',          'section',    2),
        (r'^\s*(\d{1,2}\.\d{1,3}\.\d{1,3})\s+([A-Z\u4e00-\u9fff].{3,60})$', 'subsection', 3),
        # ── 纯数字章节 "1" / "2"（与多行合并配合使用）──────
        # 仅在 merge_multiline 已把后续行拼上来后才能命中
        # 格式：数字 + 空格 + 首字母大写词组
        (r'^\s*(\d{1,2})\s+([A-Z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff ,\(\)\-]{8,70})$',
         'chapter', 1),
        # ── 带点数字编号 "1. Title"（O'Reilly/Manning）──────
        (r'^\s*(\d{1,2})[.]\s+([A-Z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff ,\(\)\-]{9,70}[^.:\n])$',
         'chapter', 1),
    ]

    def __init__(self, cfg: type = CONFIG):
        self.cfg = cfg

    # ── OCR 标准化 ────────────────────────────────────────────

    @staticmethod
    def _normalize_part(text: str) -> str:
        def fix_roman(tok: str) -> str:
            c = tok.replace('l', 'I').replace('1', 'I')
            if re.fullmatch(
                r'M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', c, re.I
            ) and c:
                return c
            return tok
        m = re.match(r'^(Part|PART)(\d+)(.*)', text)
        if m:
            return m.group(1) + ' ' + m.group(2) + m.group(3)
        m = re.match(r'^(Part|PART)\s+([IVXLivxl1]{1,6})(.*)', text, re.I)
        if m:
            return m.group(1) + ' ' + fix_roman(m.group(2)) + m.group(3)
        return text

    @staticmethod
    def _normalize_section_num(text: str) -> str:
        return re.sub(r'^(\d{1,2}\.\d{1,3})([A-Z\u4e00-\u9fff])', r'\1 \2', text)

    def _normalize(self, text: str) -> str:
        return self._normalize_section_num(self._normalize_part(text))

    # ── 过滤辅助 ─────────────────────────────────────────────

    def _is_body_sentence(self, line: str) -> bool:
        s = line.strip()
        if len(s) > 90:
            return True
        if s and s[0].islower():
            return True
        if re.search(r'[.,:;]\s+[a-z]', s):
            return True
        # "Chapter N." / "Chapter N)" → 正文引用
        if re.match(r'^(Chapter|Part|Section)\s+[\d\.]+[.)]\s*', s, re.I):
            return True
        # "Section N.N) [ref]." → 正文引用（带括号或引用数字结尾）
        if re.match(r'^Section\s+\d+[\.\d]*\s*[\)\]]', s, re.I):
            return True
        return False

    def _is_list_item(self, text: str) -> bool:
        t = text.strip()
        if t.endswith('.') or t.endswith(':'):
            return True
        m = re.match(r'^\s*\d{1,2}[.]\s+([A-Za-z]+)', t)
        if m and m.group(1).lower() in self.cfg.STEP_VERBS:
            return True
        if re.search(r'[A-Z][a-z]+,[a-z]', t):
            return True
        return False

    # ── 多行标题合并 ──────────────────────────────────────────

    @staticmethod
    def _is_standalone_heading(line: str) -> bool:
        s = line.strip()
        return bool(
            re.match(r'^\s*(Chapter|CHAPTER|C\s*H\s*A\s*P\s*T\s*E\s*R)\s+\d{1,2}\s*$', s, re.I)
            or re.match(r'^\s*(Chapter|CHAPTER)\s*$', s, re.I)
            or re.match(r'^\s*(Part|PART)\s+(\d{1,2}|I{1,3}|IV|VI{0,3}|IX|X{1,2})\s*$', s, re.I)
            # ★ 新增：孤立纯数字行（1~2位，可能是章节号）
            or re.match(r'^\s*(\d{1,2})\s*$', s)
        )

    @staticmethod
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

    def merge_multiline(self, lines: list[str]) -> list[str]:
        """合并被OCR断行的多行标题（含孤立数字行）"""
        result, i = [], 0
        while i < len(lines):
            line = lines[i]
            if not self._is_standalone_heading(line):
                result.append(line)
                i += 1
                continue

            base    = line.strip()
            s       = base
            # 孤立数字行：最多向后合并3行拼成 "1 Chapter Title"
            is_bare_chapter = bool(re.match(r'^\s*(Chapter|CHAPTER)\s*$', s, re.I))
            is_bare_digit   = bool(re.match(r'^\s*\d{1,2}\s*$', s))
            max_cont = 5 if is_bare_chapter else (3 if is_bare_digit else 2)

            j = i + 1
            while j < len(lines) and (j - i) <= max_cont:
                ns = lines[j].strip()
                if not ns or len(base) + len(ns) + 1 > 90:
                    break
                if self._is_continuation(lines[j], allow_digit=is_bare_chapter):
                    base += ' ' + ns
                    j    += 1
                else:
                    break

            # 孤立数字行：只有成功拼出标题词才保留为标题，否则原样输出
            if is_bare_digit and j == i + 1:
                result.append(line)
                i += 1
                continue

            result.append(base)
            i = j

        return result

    # ── 页眉计数 ─────────────────────────────────────────────

    @staticmethod
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

    @staticmethod
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

    # ── 主检测入口 ────────────────────────────────────────────

    def detect(
        self,
        line: str,
        header_counter: Optional[Counter] = None,
    ) -> Optional[tuple[str, int, str]]:
        stripped = line.strip()
        if not stripped or len(stripped) > 120:
            return None
        if header_counter:
            norm = re.sub(r'\s+', ' ', stripped)
            if header_counter.get(norm, 0) >= 2:
                return None
        if self._is_body_sentence(stripped):
            return None

        normalized = self._normalize(stripped)

        for pattern, level, priority in self.PATTERNS:
            if re.match(pattern, normalized, re.IGNORECASE):
                if level == 'chapter' and re.match(r'^\d{1,2}\.', normalized):
                    if self._is_list_item(normalized):
                        return None
                return level, priority, normalized

        return None

    def debug_detections(
        self,
        lines: list[str],
        header_counter: Optional[Counter] = None,
        label: str = '',
    ) -> None:
        found, lc = 0, Counter()
        print(f'\n{"─"*65}\n🔍 TitleDetector 识别结果 {label}\n{"─"*65}')
        for line in lines:
            r = self.detect(line, header_counter)
            if r:
                level, priority, title = r
                lc[level] += 1
                found += 1
                print(f'  [{level:10s}|p={priority}] {title[:65]}')
        print(f'{"─"*65}\n  共 {found} 个  分布：{dict(lc)}\n')


# ============================================================
# TextCleaner
# ============================================================

class TextCleaner:
    """文本清洗：OCR修复 + 逐行噪声过滤"""

    def __init__(self, cfg: type = CONFIG):
        self.cfg = cfg

    def is_noise(self, line: str) -> bool:
        low = line.lower().strip()
        if not low:
            return False
        for kw in self.cfg.NOISE_LINE_KEYWORDS:
            if kw in low:
                return True
        for pat in self.cfg.NOISE_LINE_PATTERNS:
            if re.search(pat, line):
                return True
        return False

    def apply_ocr_fixes(self, text: str) -> str:
        for pat, repl in self.cfg.OCR_FIXES:
            text = re.sub(pat, repl, text)
        return text

    def clean(self, text: str) -> str:
        text = self.apply_ocr_fixes(text)
        kept = [l.rstrip() for l in text.split('\n') if not self.is_noise(l)]
        return re.sub(r'\n{3,}', '\n\n', '\n'.join(kept)).strip()

    def should_skip_section(self, title: str) -> bool:
        tl = title.lower().strip()
        return any(kw in tl for kw in self.cfg.SKIP_SECTION_TITLES)

    @staticmethod
    def detect_language(text: str) -> str:
        zh = len(re.findall(r'[\u4e00-\u9fff]', text))
        en = len(re.findall(r'[A-Za-z]', text))
        return 'zh' if zh > en * 0.3 else 'en'

    @staticmethod
    def extract_original_filename(content: str) -> str:
        m = re.search(r'原始文件：(.+\.pdf)', content)
        if not m:
            return ''
        raw = m.group(1).strip()
        raw = re.sub(r'\s*\(z-library.*?\)', '', raw, flags=re.IGNORECASE)
        return re.sub(r'\.pdf$', '', raw).strip()

    @staticmethod
    def avg_line_len(text: str) -> float:
        """计算正文平均行长度（用于判断OCR质量）"""
        lines = [l.strip() for l in text.split('\n') if l.strip()
                 and not re.match(r'^---\s*第\s*\d+\s*页', l)]
        if not lines:
            return 0.0
        return sum(len(l) for l in lines) / len(lines)


# ============================================================
# CorpusBuilder
# ============================================================

class CorpusBuilder:
    """切分 + 打标签 + 输出语料库"""

    def __init__(
        self,
        cfg:            type                    = CONFIG,
        page_filter:    Optional[PageFilter]    = None,
        title_detector: Optional[TitleDetector] = None,
        text_cleaner:   Optional[TextCleaner]   = None,
    ):
        self.cfg = cfg
        self.pf  = page_filter    or PageFilter(cfg)
        self.td  = title_detector or TitleDetector(cfg)
        self.tc  = text_cleaner   or TextCleaner(cfg)

    # ── 切分（正常OCR路径）────────────────────────────────────

    def _split_chunks_normal(self, body: str) -> list[dict]:
        """正常OCR质量书籍：按章节标题切段"""
        cfg = self.cfg

        # 1. 页过滤
        pages = self.pf.split_pages(body)
        filtered_lines, skip_stats = self.pf.filter(pages)
        parts = [f'{k} {v}页' for k, v in skip_stats.items() if v]
        if parts:
            print(f'         ⏭  跳过：{" / ".join(parts)}')

        # 2. 多行标题合并
        filtered_lines = self.td.merge_multiline(filtered_lines)

        # 3. 预扫描页眉
        header_counter = self.td.build_header_counter(filtered_lines)

        # 4. 按章节标题切段
        chunks:      list[dict] = []
        cur_lines:   list[str]  = []
        cur_title    = '导言'
        cur_level    = 'intro'
        cur_priority = 99

        def _flush():
            if cur_lines:
                chunks.append({'title': cur_title, 'level': cur_level,
                                'priority': cur_priority, 'text': '\n'.join(cur_lines)})

        for line in filtered_lines:
            result = self.td.detect(line, header_counter)
            if result:
                level, priority, title = result
                _flush()
                cur_lines, cur_title, cur_level, cur_priority = [], title, level, priority
            else:
                cur_lines.append(line)
        _flush()

        # 5. 超长段落按空行再切
        def _split_oversized(lst: list[dict]) -> list[dict]:
            out = []
            for chunk in lst:
                if len(chunk['text']) <= cfg.MAX_CHUNK_CHARS:
                    out.append(chunk)
                    continue
                buf: list[str] = []
                for part in re.split(r'\n{2,}', chunk['text']):
                    buf.append(part)
                    if sum(len(p) for p in buf) >= cfg.MAX_CHUNK_CHARS // 2:
                        out.append({**chunk, 'text': '\n\n'.join(buf)})
                        buf = []
                if buf:
                    out.append({**chunk, 'text': '\n\n'.join(buf)})
            return out

        chunks = _split_oversized(chunks)

        # 6. 同节碎片合并 → 再切
        merged: list[dict] = []
        for chunk in chunks:
            cp = self.td.section_prefix(chunk['title'])
            lp = self.td.section_prefix(merged[-1]['title']) if merged else None
            if cp and cp == lp and merged[-1]['level'] == chunk['level']:
                merged[-1]['text'] += '\n\n' + chunk['text']
            else:
                merged.append(chunk)

        return _split_oversized(merged)

    # ── 切分（逐词OCR降级路径）───────────────────────────────

    def _split_chunks_poor_ocr(self, body: str) -> list[dict]:
        """
        极差OCR（每行只有1~3个单词）的降级策略：
        按页重新拼合文字，以页为单位输出段落。
        标题从拼合后的页首行推断。
        """
        cfg   = self.cfg
        pages = self.pf.split_pages(body)
        _, skip_stats = self.pf.filter(pages)  # 仍过滤明显废页，但用原始pages
        parts = [f'{k} {v}页' for k, v in skip_stats.items() if v]
        if parts:
            print(f'         ⏭  跳过（降级模式）：{" / ".join(parts)}')

        print(f'         ⚠️  检测到逐词OCR，启用按页合并策略')

        chunks: list[dict] = []
        # 每5页合并成一段（避免每页太短被丢弃）
        GROUP = 5
        page_texts: list[str] = []

        for page_lines in pages:
            # 跳过废页
            if (self.pf.score_frontmatter(page_lines) >= cfg.FRONTMATTER_THRESHOLD
                    or self.pf.score_toc(page_lines) >= cfg.TOC_THRESHOLD):
                continue
            # 把单词行重新拼成段落（按空行分组）
            words = [l.strip() for l in page_lines if l.strip()
                     and not re.match(r'^---', l)]
            if words:
                page_texts.append(' '.join(words))

        # 按GROUP分组
        for i in range(0, len(page_texts), GROUP):
            group = page_texts[i:i + GROUP]
            text  = '\n\n'.join(group)
            chunks.append({
                'title':    f'页段 {i+1}–{min(i+GROUP, len(page_texts))}',
                'level':    'page_group',
                'priority': 5,
                'text':     text,
            })

        return chunks

    # ── 统一切分入口 ─────────────────────────────────────────

    def _split_chunks(self, body: str) -> list[dict]:
        avg = self.tc.avg_line_len(body)
        if avg < self.cfg.POOR_OCR_AVG_LINE_LEN:
            return self._split_chunks_poor_ocr(body)
        return self._split_chunks_normal(body)

    # ── 打标签 ────────────────────────────────────────────────

    def _build_record(
        self,
        chunk:     dict,
        book_info: dict,
        chunk_idx: int,
        total:     int,
    ) -> Optional[dict]:
        if self.tc.should_skip_section(chunk['title']):
            return None
        text = self.tc.clean(chunk['text'])
        if len(text) < self.cfg.MIN_CHUNK_CHARS:
            return None
        return {
            'book_id':       book_info['book_id'],
            'book_title':    book_info['title'],
            'language':      book_info['language'],
            'source_file':   book_info['source_file'],
            'chapter_title': chunk['title'],
            'chapter_level': chunk['level'],
            'chunk_index':   chunk_idx,
            'total_chunks':  total,
            'text':          text,
            'char_count':    len(text),
            'created_at':    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    # ── 单书处理 ─────────────────────────────────────────────

    def process_book(self, txt_path: Path, book_id: int) -> list[dict]:
        content       = txt_path.read_text(encoding='utf-8', errors='ignore')
        raw_title     = self.tc.extract_original_filename(content)
        display_title = raw_title or txt_path.stem
        body          = '\n'.join(content.split('\n')[5:])
        lang          = self.tc.detect_language(body[:5000])

        book_info = {
            'book_id':     f'book_{book_id:02d}',
            'title':       display_title,
            'language':    lang,
            'source_file': txt_path.name,
        }

        chunks = self._split_chunks(body)
        if not chunks:
            chunks = [{'title': display_title, 'level': 'book', 'priority': 1, 'text': body}]

        records: list[dict] = []
        for chunk in chunks:
            rec = self._build_record(chunk, book_info, 0, 0)
            if rec:
                records.append(rec)

        total = len(records)
        for idx, rec in enumerate(records, 1):
            rec['chunk_index']  = idx
            rec['total_chunks'] = total

        return records

    # ── 输出 ─────────────────────────────────────────────────

    def save(self, records: list[dict], output_dir: Path) -> tuple[Path, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)

        # ── 按书分组 ──────────────────────────────────────────
        book_groups: dict = defaultdict(list)
        for r in records:
            book_groups[r['book_id']].append(r)

        # ── 每本书输出一个独立 JSON ────────────────────────────
        per_book_dir = output_dir / 'per_book'
        per_book_dir.mkdir(exist_ok=True)
        for book_id, book_records in sorted(book_groups.items()):
            stem     = Path(book_records[0]['source_file']).stem  # 如 01_DATA-DRIVEN
            out_path = per_book_dir / f'{stem}.json'
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(book_records, f, ensure_ascii=False, indent=2)

        # ── 同时保留合并版（方便整体检索）────────────────────
        corpus_path = output_dir / 'corpus.json'
        with open(corpus_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        # ── 统计 CSV ──────────────────────────────────────────
        book_stats: dict = defaultdict(
            lambda: {'chunks': 0, 'total_chars': 0, 'file': '', 'language': ''})
        for r in records:
            bs = book_stats[r['book_id']]
            bs['chunks']      += 1
            bs['total_chars'] += r['char_count']
            bs['file']         = r['source_file']
            bs['language']     = r['language']

        stats_rows = [{'book_id': bid, **v} for bid, v in sorted(book_stats.items())]
        stats_path = output_dir / 'corpus_stats.csv'
        with open(stats_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(
                f, fieldnames=['book_id','file','language','chunks','total_chars'])
            writer.writeheader()
            writer.writerows(stats_rows)

        print(f'\n📁 每本书独立文件：{per_book_dir}')
        for book_id, book_records in sorted(book_groups.items()):
            stem = Path(book_records[0]['source_file']).stem
            print(f'   {stem}.json  ({len(book_records)} 段)')

        return corpus_path, stats_path

    # ── 调试统一入口 ──────────────────────────────────────────

    def run_debug(self, txt_path: Path) -> None:
        """一键运行全部调试：页面分数 + 高频页眉 + 标题识别"""
        print(f'\n{"="*65}\n  调试：{txt_path.name}\n{"="*65}')
        content = txt_path.read_text(encoding='utf-8', errors='ignore')
        body    = '\n'.join(content.split('\n')[5:])

        avg = self.tc.avg_line_len(body)
        print(f'  平均行长：{avg:.1f} 字符  '
              f'（< {self.cfg.POOR_OCR_AVG_LINE_LEN} 则启用降级模式）')

        pages = self.pf.split_pages(body)
        self.pf.debug_scores(txt_path)

        filtered, _ = self.pf.filter(pages)
        filtered = self.td.merge_multiline(filtered)
        hc = self.td.build_header_counter(filtered)

        print(f'\n🔍 高频行 TOP25（≥2次视为页眉）：')
        for text, cnt in hc.most_common(25):
            if cnt >= 2:
                print(f'  {cnt:3d}× {repr(text[:65])}')

        self.td.debug_detections(filtered, hc, label=f'— {txt_path.name}')


# ============================================================
# main
# ============================================================

def main():
    cfg        = CONFIG
    input_dir  = Path(cfg.INPUT_DIR)
    output_dir = Path(cfg.OUTPUT_DIR)
    builder    = CorpusBuilder(cfg)

    txt_files = sorted([f for f in input_dir.glob('*.txt') if not f.name.startswith('_')])
    if not txt_files:
        print(f'❌ 未找到 TXT 文件：{input_dir.resolve()}')
        return

    print(f'✅ 找到 {len(txt_files)} 本书，开始处理...\n')

    # ── 调试开关：取消注释对某本书运行一键调试 ──────────────────
    # builder.run_debug(txt_files[0])
    # return

    all_records:   list[dict] = []
    problem_books: list[str]  = []
    start = time.time()

    for book_id, txt_path in enumerate(txt_files, 1):
        print(f'[{book_id:02d}/{len(txt_files)}] {txt_path.name}')
        records = builder.process_book(txt_path, book_id)
        all_records.extend(records)

        lang       = records[0]['language'] if records else '?'
        total_char = sum(r['char_count'] for r in records)
        level_dist = Counter(r['chapter_level'] for r in records)
        dist_str   = '  '.join(f'{lv}:{cnt}' for lv, cnt in sorted(level_dist.items()))

        print(f'         → {len(records):>4} 段  语言：{lang}  字符：{total_char:,}')
        print(f'         层级：{dist_str}')

        n_intro = level_dist.get('intro', 0)
        if records and n_intro / len(records) > 0.5:
            problem_books.append(
                f'{txt_path.name}：intro 占比 {n_intro}/{len(records)}，章节识别可能失败')

    corpus_path, stats_path = builder.save(all_records, output_dir)

    elapsed     = time.time() - start
    total_chars = sum(r['char_count'] for r in all_records)

    print(f'\n{"="*65}')
    print(f'🎉 语料库构建完成！'
          f'总段落：{len(all_records):,}  总字符：{total_chars:,}  耗时：{elapsed:.1f}s')
    print(f'\n📄 输出：\n   {corpus_path}\n   {stats_path}')

    print(f'\n🔍 前20段标题预览：')
    for r in all_records[:20]:
        print(f"  [{r['chunk_index']:03d}] [{r['chapter_level']:10s}] "
              f"{r['chapter_title'][:55]:<55} ({r['char_count']} 字符)")

    level_counts: Counter = Counter(r['chapter_level'] for r in all_records)
    print(f'\n📊 各层级段落数统计：')
    for lv, cnt in level_counts.most_common():
        bar = '█' * min(cnt // 10, 40)
        print(f'   {lv:12s}: {cnt:>5} 段  {bar}')

    if problem_books:
        print(f'\n⚠️  以下书籍章节识别可能异常：')
        for msg in problem_books:
            print(f'   • {msg}')
        print('\n   调试：取消 main() 中注释 → builder.run_debug(txt_path)')
    else:
        print('\n✅ 所有书籍层级分布合理。')


if __name__ == '__main__':
    main()

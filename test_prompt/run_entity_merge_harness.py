import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = Path(__file__).resolve().parent / "results"
MERGE_RESULTS_DIR = RESULTS_DIR / "entity_merge"
ROUNDS_DIR = Path(__file__).resolve().parent / "task11_rounds"
DEFAULT_RESULTS_FILE = RESULTS_DIR / "batches" / "batch_extract_batch_v4_all15_deduped.jsonl"
DEFAULT_SEED_ALIAS_FILE = Path(__file__).resolve().parent / "entity_merge_seed_aliases.json"
DEFAULT_AMBIGUOUS_ACRONYMS_FILE = Path(__file__).resolve().parent / "entity_merge_ambiguous_acronyms.json"

LATIN_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")
PAREN_ALIAS_RE = re.compile(r"^(?P<long>.+?)\s*\((?P<short>[^()]{2,24})\)\s*$")
SIMPLE_LATIN_PHRASE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 -]*$")
STOPWORDS = {
    "a",
    "an",
    "the",
    "of",
    "for",
    "and",
    "or",
    "to",
    "in",
    "on",
    "with",
}
SIGNAL_WEIGHTS = {
    "surface_key_match": 0.9,
    "plural_variant": 0.82,
    "seed_alias_match": 1.1,
    "parenthetical_alias": 1.0,
    "acronym_longform": 0.95,
    "ambiguous_acronym": 0.35,
    "surface_containment": 0.22,
    "head_word_match": 0.12,
    "token_overlap_match": 0.24,
    "definition_overlap": 0.16,
}
EXPLICIT_ALIAS_SIGNALS = {"seed_alias_match", "parenthetical_alias", "acronym_longform"}
ROLE_KEYWORDS = {
    "algorithm": {
        "algorithm",
        "algorithms",
        "method",
        "methods",
        "procedure",
        "procedures",
        "framework",
        "frameworks",
        "模型",
        "算法",
        "方法",
    },
    "metric": {
        "coefficient",
        "coefficients",
        "score",
        "scores",
        "rate",
        "rates",
        "ratio",
        "ratios",
        "metric",
        "metrics",
        "index",
        "indices",
        "coefficient",
        "系数",
        "得分",
        "评分",
        "比率",
        "指标",
    },
    "structure": {
        "matrix",
        "matrices",
        "vector",
        "vectors",
        "table",
        "tables",
        "matrixes",
        "矩阵",
        "向量",
        "表",
        "表格",
    },
    "task": {
        "problem",
        "problems",
        "task",
        "tasks",
        "问题",
        "任务",
    },
    "method_or_task": {
        "analysis",
        "analyses",
        "testing",
        "test",
        "tests",
        "study",
        "studies",
        "analysis",
        "分析",
        "测试",
        "检验",
        "研究",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Task11 entity-merge harness: extract entity forms, generate merge candidates, and write review artifacts."
    )
    parser.add_argument(
        "--results-file",
        default=str(DEFAULT_RESULTS_FILE),
        help="Deduped extraction JSONL file. Defaults to the final all-15-books batch.",
    )
    parser.add_argument(
        "--round-name",
        default=None,
        help="Optional round label. Defaults to task11_merge_<timestamp>.",
    )
    parser.add_argument(
        "--seed-alias-file",
        default=str(DEFAULT_SEED_ALIAS_FILE),
        help="Curated alias seed JSON file.",
    )
    parser.add_argument(
        "--ambiguous-acronyms-file",
        default=str(DEFAULT_AMBIGUOUS_ACRONYMS_FILE),
        help="JSON file listing ambiguous acronyms that should not be auto-merged globally.",
    )
    parser.add_argument(
        "--max-review-samples",
        type=int,
        default=60,
        help="Maximum uncertain samples to emit for review.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print high-level counts without writing files.",
    )
    return parser.parse_args()


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text or "").strip()
    text = text.replace("–", "-").replace("—", "-").replace("／", "/")
    return text


def build_surface_key(name):
    text = normalize_text(name).casefold()
    kept = []
    for char in text:
        if char.isalnum() or CJK_CHAR_RE.match(char) or char in {"+", "&"}:
            kept.append(char)
    return "".join(kept)


def tokenize_name(name):
    text = normalize_text(name)
    tokens = LATIN_TOKEN_RE.findall(text)
    cjk_tokens = CJK_CHAR_RE.findall(text)
    out = [token.casefold() for token in tokens]
    out.extend(cjk_tokens)
    return out


def content_tokens(name):
    return [token for token in tokenize_name(name) if token not in STOPWORDS]


def acronym_for(name):
    tokens = [token for token in LATIN_TOKEN_RE.findall(normalize_text(name)) if token]
    if len(tokens) < 2:
        return None
    acronym = "".join(token[0] for token in tokens).upper()
    return acronym if len(acronym) >= 2 else None


def acronym_token(name):
    text = normalize_text(name)
    letters = "".join(char for char in text if char.isalnum()).upper()
    if 2 <= len(letters) <= 6 and letters.isascii():
        return letters
    return None


def head_word(name):
    tokens = [singularize_token(token) for token in LATIN_TOKEN_RE.findall(normalize_text(name))]
    tokens = [token for token in tokens if token not in STOPWORDS]
    if len(tokens) < 2:
        return None
    return tokens[-1]


def singularize_token(token):
    token = token.casefold()
    if len(token) <= 3:
        return token
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("es") and len(token) > 4 and token[-3] in {"s", "x", "z"}:
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def stable_id(prefix, *parts):
    payload = "||".join(parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha1(payload).hexdigest()[:12]}"


def choose_canonical_name(forms, seed_canonical_name=None):
    if seed_canonical_name:
        return seed_canonical_name
    ranked = sorted(
        forms,
        key=lambda form: (
            -form["mention_count"],
            -form["book_count"],
            len(form["name"]),
            form["name"].casefold(),
        ),
    )
    return ranked[0]["name"]


def infer_merge_role(name, entity_type):
    text = normalize_text(name)
    tokens = {token.casefold() for token in LATIN_TOKEN_RE.findall(text)}
    for role in ("metric", "structure", "task"):
        keywords = ROLE_KEYWORDS[role]
        if tokens & keywords:
            return role
        if any(keyword in text for keyword in keywords if not keyword.isascii()):
            return role

    if entity_type == "algorithm":
        return "algorithm"

    keywords = ROLE_KEYWORDS["algorithm"]
    if tokens & keywords:
        return "algorithm"
    if any(keyword in text for keyword in keywords if not keyword.isascii()):
        return "algorithm"

    keywords = ROLE_KEYWORDS["method_or_task"]
    if tokens & keywords:
        return "method_or_task"
    if any(keyword in text for keyword in keywords if not keyword.isascii()):
        return "method_or_task"

    lowered = text.casefold()
    if lowered.endswith("ing"):
        return "method_or_task"

    return entity_type


def build_forms(rows):
    form_index = {}
    mention_rows = []

    for row in rows:
        if row.get("status") != "success":
            continue

        for entity in row.get("result", {}).get("entities", []):
            name = normalize_text(entity.get("name", ""))
            entity_type = entity.get("type", "")
            if not name or not entity_type:
                continue

            form_id = stable_id("form", entity_type, name)
            mention_id = stable_id(
                "mention",
                row["book_file"],
                str(row["chunk_index"]),
                entity.get("id", ""),
                entity_type,
                name,
            )
            definition = normalize_text(entity.get("definition", ""))
            mention = {
                "mention_id": mention_id,
                "form_id": form_id,
                "name": name,
                "type": entity_type,
                "definition": definition,
                "book_file": row["book_file"],
                "book_title": row["book_title"],
                "chapter_title": row["chapter_title"],
                "chunk_index": row["chunk_index"],
                "language": row.get("language"),
            }
            mention_rows.append(mention)

            if form_id not in form_index:
                form_index[form_id] = {
                    "form_id": form_id,
                    "name": name,
                    "type": entity_type,
                    "surface_key": build_surface_key(name),
                    "tokens": tokenize_name(name),
                    "content_tokens": content_tokens(name),
                    "acronym": acronym_for(name),
                    "head_word": head_word(name),
                    "merge_role": infer_merge_role(name, entity_type),
                    "mention_count": 0,
                    "books": set(),
                    "languages": Counter(),
                    "definitions": Counter(),
                    "sample_sources": [],
                }

            form = form_index[form_id]
            form["mention_count"] += 1
            form["books"].add(row["book_file"])
            if row.get("language"):
                form["languages"][row["language"]] += 1
            if definition:
                form["definitions"][definition] += 1
            if len(form["sample_sources"]) < 5:
                form["sample_sources"].append(
                    {
                        "book_file": row["book_file"],
                        "chapter_title": row["chapter_title"],
                        "chunk_index": row["chunk_index"],
                    }
                )

    forms = []
    for form in form_index.values():
        forms.append(
            {
                "form_id": form["form_id"],
                "name": form["name"],
                "type": form["type"],
                "surface_key": form["surface_key"],
                "tokens": form["tokens"],
                "content_tokens": form["content_tokens"],
                "acronym": form["acronym"],
                "head_word": form["head_word"],
                "merge_role": form["merge_role"],
                "mention_count": form["mention_count"],
                "book_count": len(form["books"]),
                "books": sorted(form["books"]),
                "languages": dict(form["languages"]),
                "top_definitions": [definition for definition, _ in form["definitions"].most_common(3)],
                "sample_sources": form["sample_sources"],
            }
        )

    forms.sort(key=lambda form: (-form["book_count"], -form["mention_count"], form["type"], form["name"].casefold()))
    mention_rows.sort(key=lambda row: (row["book_file"], row["chunk_index"], row["name"].casefold()))
    return mention_rows, forms


def load_seed_aliases(path):
    path = Path(path)
    if not path.exists():
        return {}, []

    payload = json.loads(path.read_text(encoding="utf-8"))
    alias_to_cluster = {}
    clusters = []

    for item in payload:
        canonical_name = normalize_text(item["canonical_name"])
        entity_type = item["type"]
        aliases = sorted({normalize_text(alias) for alias in item["aliases"] if normalize_text(alias)})
        cluster_id = stable_id("seed", entity_type, canonical_name)
        cluster = {
            "seed_cluster_id": cluster_id,
            "canonical_name": canonical_name,
            "type": entity_type,
            "aliases": aliases,
        }
        clusters.append(cluster)
        for alias in aliases:
            alias_to_cluster[(entity_type, alias.casefold())] = cluster

    return alias_to_cluster, clusters


def load_ambiguous_acronyms(path):
    path = Path(path)
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {normalize_text(item).upper() for item in payload if normalize_text(item)}


def pair_key(left_id, right_id):
    return tuple(sorted((left_id, right_id)))


def add_candidate(store, left, right, signal, seed_canonical_name=None):
    key = pair_key(left["form_id"], right["form_id"])
    existing = store.get(key)
    if existing is None:
        existing = {
            "candidate_id": stable_id("cand", left["form_id"], right["form_id"]),
            "left_form_id": left["form_id"],
            "right_form_id": right["form_id"],
            "left_name": left["name"],
            "right_name": right["name"],
            "left_type": left["type"],
            "right_type": right["type"],
            "left_merge_role": left.get("merge_role"),
            "right_merge_role": right.get("merge_role"),
            "seed_canonical_name": seed_canonical_name,
            "left_book_count": left["book_count"],
            "right_book_count": right["book_count"],
            "left_mention_count": left["mention_count"],
            "right_mention_count": right["mention_count"],
            "left_surface_key": left["surface_key"],
            "right_surface_key": right["surface_key"],
            "left_top_definitions": left["top_definitions"],
            "right_top_definitions": right["top_definitions"],
            "signals": [],
            "score_raw": 0.0,
            "strongest_signal": None,
            "strongest_weight": 0.0,
        }
        store[key] = existing

    if signal not in existing["signals"]:
        weight = SIGNAL_WEIGHTS[signal]
        existing["signals"].append(signal)
        existing["score_raw"] += weight
        if weight > existing["strongest_weight"]:
            existing["strongest_weight"] = weight
            existing["strongest_signal"] = signal

    if seed_canonical_name and not existing.get("seed_canonical_name"):
        existing["seed_canonical_name"] = seed_canonical_name


def surface_variant_only(left_name, right_name):
    return build_surface_key(left_name) == build_surface_key(right_name) and normalize_text(left_name) != normalize_text(right_name)


def shared_token_ratio(left_tokens, right_tokens):
    left = set(left_tokens)
    right = set(right_tokens)
    if not left or not right:
        return 0.0
    return len(left & right) / max(len(left), len(right))


def definition_overlap_ratio(left_defs, right_defs):
    if not left_defs or not right_defs:
        return 0.0
    left = set(content_tokens(" ".join(left_defs)))
    right = set(content_tokens(" ".join(right_defs)))
    if not left or not right:
        return 0.0
    return len(left & right) / max(len(left), len(right))


def plural_variant_match(left_name, right_name):
    if not SIMPLE_LATIN_PHRASE_RE.fullmatch(normalize_text(left_name)):
        return False
    if not SIMPLE_LATIN_PHRASE_RE.fullmatch(normalize_text(right_name)):
        return False
    left_tokens = LATIN_TOKEN_RE.findall(normalize_text(left_name))
    right_tokens = LATIN_TOKEN_RE.findall(normalize_text(right_name))
    if not left_tokens or not right_tokens:
        return False
    if len(left_tokens) != len(right_tokens):
        return False
    left_singular = [singularize_token(token) for token in left_tokens]
    right_singular = [singularize_token(token) for token in right_tokens]
    return (
        left_singular == right_singular
        and normalize_text(left_name).casefold() != normalize_text(right_name).casefold()
        and any(left.casefold() != right.casefold() for left, right in zip(left_tokens, right_tokens))
    )


def singular_token_key(name):
    if not SIMPLE_LATIN_PHRASE_RE.fullmatch(normalize_text(name)):
        return None
    tokens = LATIN_TOKEN_RE.findall(normalize_text(name))
    if not tokens:
        return None
    return tuple(singularize_token(token) for token in tokens)


def finalize_candidates(store):
    rows = []
    for row in store.values():
        signals = set(row["signals"])
        score = row["score_raw"]

        if score < 0.45:
            continue
        if "ambiguous_acronym" in signals:
            row["decision"] = "uncertain"
            row["reason"] = "ambiguous_acronym"
            row["confidence"] = min(0.8, score)
        elif row["left_type"] != row["right_type"]:
            row["decision"] = "keep_separate"
            row["reason"] = "entity_type_mismatch"
            row["confidence"] = 1.0
        elif row["left_merge_role"] != row["right_merge_role"] and not (signals & EXPLICIT_ALIAS_SIGNALS):
            row["decision"] = "keep_separate"
            row["reason"] = "merge_role_mismatch"
            row["confidence"] = 0.99
        elif score >= 0.85:
            row["decision"] = "merge"
            row["reason"] = "scored_merge"
            row["confidence"] = min(0.99, score)
        else:
            row["decision"] = "uncertain"
            row["reason"] = "scored_review"
            row["confidence"] = min(0.89, score)

        rows.append(row)

    rows.sort(
        key=lambda row: (
            {"merge": 0, "uncertain": 1, "keep_separate": 2}[row["decision"]],
            row["left_type"],
            row["left_name"].casefold(),
            row["right_name"].casefold(),
        )
    )
    return rows


def generate_candidates(forms, alias_to_cluster, ambiguous_acronyms):
    store = {}

    by_surface = defaultdict(list)
    by_type = defaultdict(list)
    by_acronym = defaultdict(list)
    by_acronym_token = defaultdict(list)
    by_head = defaultdict(list)

    for form in forms:
        by_type[form["type"]].append(form)
        by_surface[(form["type"], form["surface_key"])].append(form)
        if form["acronym"]:
            by_acronym[(form["type"], form["acronym"])].append(form)
        token = acronym_token(form["name"])
        if token:
            by_acronym_token[(form["type"], token)].append(form)
        if form["head_word"]:
            by_head[(form["type"], form["head_word"])].append(form)

    for (_, surface_key), bucket in by_surface.items():
        if len(bucket) < 2:
            continue
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                left = bucket[i]
                right = bucket[j]
                if surface_variant_only(left["name"], right["name"]):
                    add_candidate(store, left, right, "surface_key_match")

    for entity_type, typed_forms in by_type.items():
        plural_buckets = defaultdict(list)
        for form in typed_forms:
            key = singular_token_key(form["name"])
            if key is not None:
                plural_buckets[key].append(form)

        for bucket in plural_buckets.values():
            if len(bucket) < 2:
                continue
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    left = bucket[i]
                    right = bucket[j]
                    if plural_variant_match(left["name"], right["name"]):
                        add_candidate(store, left, right, "plural_variant")

    seed_buckets = defaultdict(list)
    for form in forms:
        cluster = alias_to_cluster.get((form["type"], form["name"].casefold()))
        if cluster is not None:
            seed_buckets[cluster["seed_cluster_id"]].append((cluster, form))

    for items in seed_buckets.values():
        if len(items) < 2:
            continue
        cluster = items[0][0]
        bucket = [form for _, form in items]
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                add_candidate(store, bucket[i], bucket[j], "seed_alias_match", cluster["canonical_name"])

    seen_paren_pairs = set()
    for form in forms:
        match = PAREN_ALIAS_RE.match(form["name"])
        if not match:
            continue
        long_name = normalize_text(match.group("long"))
        short_name = normalize_text(match.group("short"))
        for candidate in by_type[form["type"]]:
            if candidate["form_id"] == form["form_id"]:
                continue
            if candidate["name"] not in {long_name, short_name}:
                continue
            key = pair_key(form["form_id"], candidate["form_id"])
            if key in seen_paren_pairs:
                continue
            seen_paren_pairs.add(key)
            add_candidate(store, form, candidate, "parenthetical_alias", long_name)

    for (entity_type, acronym), short_forms in by_acronym.items():
        short_token_forms = by_acronym_token.get((entity_type, acronym), [])
        if not short_token_forms:
            continue
        for form in by_type[entity_type]:
            if form["form_id"] in {item["form_id"] for item in short_forms}:
                continue
            if acronym_for(form["name"]) != acronym:
                continue
            for short_form in short_token_forms:
                if acronym_token(short_form["name"]) != acronym:
                    continue
                if acronym in ambiguous_acronyms:
                    add_candidate(store, short_form, form, "ambiguous_acronym", form["name"])
                else:
                    add_candidate(store, short_form, form, "acronym_longform", form["name"])

    for (_, head), bucket in by_head.items():
        if len(bucket) < 2:
            continue
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                left = bucket[i]
                right = bucket[j]
                ratio = shared_token_ratio(left["content_tokens"], right["content_tokens"])
                if ratio >= 0.34:
                    add_candidate(store, left, right, "head_word_match")

    for entity_type, typed_forms in by_type.items():
        token_buckets = defaultdict(list)
        for form in typed_forms:
            if form["surface_key"]:
                token_buckets[form["surface_key"][:8]].append(form)

        for bucket in token_buckets.values():
            if len(bucket) < 2:
                continue
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    left = bucket[i]
                    right = bucket[j]
                    token_ratio = shared_token_ratio(left["content_tokens"], right["content_tokens"])
                    if left["surface_key"] in right["surface_key"] or right["surface_key"] in left["surface_key"]:
                        if token_ratio >= 0.5:
                            add_candidate(store, left, right, "surface_containment")
                    elif token_ratio >= 0.67:
                        add_candidate(store, left, right, "token_overlap_match")

                    if definition_overlap_ratio(left["top_definitions"], right["top_definitions"]) >= 0.5:
                        add_candidate(store, left, right, "definition_overlap")

    return finalize_candidates(store)


class UnionFind:
    def __init__(self):
        self.parent = {}

    def add(self, item):
        self.parent.setdefault(item, item)

    def find(self, item):
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left, right):
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left


def build_clusters(forms, candidate_rows):
    form_by_id = {form["form_id"]: form for form in forms}
    union_find = UnionFind()
    seed_canonical_by_root = {}

    for form in forms:
        union_find.add(form["form_id"])

    for row in candidate_rows:
        if row["decision"] != "merge":
            continue
        union_find.union(row["left_form_id"], row["right_form_id"])

    for row in candidate_rows:
        if row["decision"] != "merge" or not row.get("seed_canonical_name"):
            continue
        root = union_find.find(row["left_form_id"])
        seed_canonical_by_root[root] = row["seed_canonical_name"]

    buckets = defaultdict(list)
    for form in forms:
        buckets[union_find.find(form["form_id"])].append(form)

    clusters = []
    for root, items in buckets.items():
        canonical_name = choose_canonical_name(items, seed_canonical_by_root.get(root))
        cluster_id = stable_id("cluster", items[0]["type"], canonical_name)
        total_mentions = sum(item["mention_count"] for item in items)
        total_books = sorted({book for item in items for book in item["books"]})
        clusters.append(
            {
                "cluster_id": cluster_id,
                "canonical_name": canonical_name,
                "type": items[0]["type"],
                "form_count": len(items),
                "mention_count": total_mentions,
                "book_count": len(total_books),
                "books": total_books,
                "member_forms": [
                    {
                        "form_id": item["form_id"],
                        "name": item["name"],
                        "mention_count": item["mention_count"],
                        "book_count": item["book_count"],
                    }
                    for item in sorted(items, key=lambda form: (-form["mention_count"], form["name"].casefold()))
                ],
            }
        )

    clusters.sort(key=lambda row: (-row["form_count"], -row["mention_count"], row["canonical_name"].casefold()))
    return clusters


def build_review_samples(candidate_rows, max_samples):
    risky = [row for row in candidate_rows if row["decision"] == "uncertain"]
    risky.sort(
        key=lambda row: (
            -(row["left_book_count"] + row["right_book_count"]),
            -(row["left_mention_count"] + row["right_mention_count"]),
            row["reason"],
            row["left_name"].casefold(),
        )
    )
    return risky[:max_samples]


def board_name_for_candidate(row):
    reason = row["reason"]
    if reason in {"entity_type_mismatch", "merge_role_mismatch"}:
        return "blocked_by_role"
    signal = row.get("strongest_signal")
    if reason == "ambiguous_acronym" or signal == "ambiguous_acronym":
        return "ambiguous_acronyms"
    if signal == "surface_key_match":
        return "surface_variants"
    if signal == "plural_variant":
        return "inflection_variants"
    if signal in {"seed_alias_match", "parenthetical_alias", "acronym_longform"}:
        return "explicit_aliases"
    if signal in {"head_word_match", "token_overlap_match", "definition_overlap"}:
        return "recall_review"
    return "risky_review"


def build_boards(candidate_rows):
    boards = defaultdict(list)
    for row in candidate_rows:
        boards[board_name_for_candidate(row)].append(row)
    return {name: rows for name, rows in boards.items()}


def build_cluster_backlog(clusters):
    backlog = []
    for cluster in clusters:
        if cluster["form_count"] < 2 or cluster["book_count"] < 2:
            continue
        backlog.append(
            {
                "cluster_id": cluster["cluster_id"],
                "canonical_name": cluster["canonical_name"],
                "type": cluster["type"],
                "form_count": cluster["form_count"],
                "book_count": cluster["book_count"],
                "member_names": [member["name"] for member in cluster["member_forms"]],
            }
        )
    backlog.sort(key=lambda row: (-row["book_count"], -row["form_count"], row["canonical_name"].casefold()))
    return backlog


def build_recall_backlog(forms, candidate_rows):
    covered_pairs = {pair_key(row["left_form_id"], row["right_form_id"]) for row in candidate_rows}
    head_buckets = defaultdict(list)
    for form in forms:
        if form["head_word"]:
            head_buckets[(form["type"], form["head_word"])].append(form)

    backlog = []
    for (entity_type, head), bucket in head_buckets.items():
        if len(bucket) < 3:
            continue
        unresolved = 0
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                if pair_key(bucket[i]["form_id"], bucket[j]["form_id"]) not in covered_pairs:
                    unresolved += 1
        if unresolved == 0:
            continue
        backlog.append(
            {
                "type": entity_type,
                "head_word": head,
                "form_count": len(bucket),
                "unresolved_pairs": unresolved,
                "member_names": [item["name"] for item in sorted(bucket, key=lambda form: (-form["mention_count"], form["name"].casefold()))[:12]],
            }
        )
    backlog.sort(key=lambda row: (-row["unresolved_pairs"], -row["form_count"], row["head_word"]))
    return backlog


def render_report(round_name, summary, review_samples, top_clusters, boards, recall_backlog):
    lines = [
        f"# {round_name}",
        "",
        "## 总结",
        "",
        f"- 输入文件：`{summary['input_results_file']}`",
        f"- 原始实体 mention：`{summary['raw_entity_mentions']}`",
        f"- 唯一实体 form：`{summary['unique_entity_forms']}`",
        f"- 自动 merge 决策：`{summary['merge_decisions']}`",
        f"- uncertain 候选：`{summary['uncertain_candidates']}`",
        f"- 合并后 cluster：`{summary['clusters_after_merge']}`",
        f"- 节点净减少：`{summary['node_reduction']}`",
        "",
        "## 设计口径",
        "",
        "- 本轮只自动合并高置信等价项：表面规范化变体、seed alias、括号别名、明确 acronym-longform。",
        "- 共享词根、头词、定义相近项先进入召回层，再由 score + gate 决定 merge / review / block。",
        "",
        "## 板块统计",
        "",
        f"- surface_variants：`{len(boards.get('surface_variants', []))}`",
        f"- inflection_variants：`{len(boards.get('inflection_variants', []))}`",
        f"- explicit_aliases：`{len(boards.get('explicit_aliases', []))}`",
        f"- ambiguous_acronyms：`{len(boards.get('ambiguous_acronyms', []))}`",
        f"- blocked_by_role：`{len(boards.get('blocked_by_role', []))}`",
        f"- recall_review：`{len(boards.get('recall_review', []))}`",
        f"- risky_review：`{len(boards.get('risky_review', []))}`",
        "",
        "## 高风险待审样本",
        "",
    ]

    if not review_samples:
        lines.append("- 无")
    else:
        for row in review_samples:
            lines.append(
                f"- `{row['left_name']}` ↔ `{row['right_name']}` | type=`{row['left_type']}` | reason=`{row['reason']}` | confidence=`{row['confidence']}`"
            )

    lines.extend(["", "## 重点合并簇", ""])

    if not top_clusters:
        lines.append("- 无")
    else:
        for cluster in top_clusters:
            member_names = ", ".join(member["name"] for member in cluster["member_forms"][:8])
            lines.append(
                f"- `{cluster['canonical_name']}` | members=`{cluster['form_count']}` | mentions=`{cluster['mention_count']}` | books=`{cluster['book_count']}` | {member_names}"
            )

    lines.extend(["", "## Recall Backlog", ""])
    if not recall_backlog:
        lines.append("- 无")
    else:
        for row in recall_backlog[:20]:
            member_names = ", ".join(row["member_names"][:8])
            lines.append(
                f"- head=`{row['head_word']}` | type=`{row['type']}` | forms=`{row['form_count']}` | unresolved_pairs=`{row['unresolved_pairs']}` | {member_names}"
            )

    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    input_path = Path(args.results_file).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Results file not found: {input_path}")

    rows = load_jsonl(input_path)
    mention_rows, forms = build_forms(rows)
    alias_to_cluster, seed_clusters = load_seed_aliases(args.seed_alias_file)
    ambiguous_acronyms = load_ambiguous_acronyms(args.ambiguous_acronyms_file)
    candidate_rows = generate_candidates(forms, alias_to_cluster, ambiguous_acronyms)
    clusters = build_clusters(forms, candidate_rows)
    review_samples = build_review_samples(candidate_rows, args.max_review_samples)
    boards = build_boards(candidate_rows)
    cluster_backlog = build_cluster_backlog(clusters)
    recall_backlog = build_recall_backlog(forms, candidate_rows)

    summary = {
        "input_results_file": str(input_path),
        "raw_entity_mentions": len(mention_rows),
        "unique_entity_forms": len(forms),
        "seed_alias_clusters": len(seed_clusters),
        "ambiguous_acronyms": sorted(ambiguous_acronyms),
        "candidate_pairs": len(candidate_rows),
        "merge_decisions": sum(1 for row in candidate_rows if row["decision"] == "merge"),
        "uncertain_candidates": sum(1 for row in candidate_rows if row["decision"] == "uncertain"),
        "blocked_candidates": sum(1 for row in candidate_rows if row["decision"] == "keep_separate"),
        "clusters_after_merge": len(clusters),
        "node_reduction": len(forms) - len(clusters),
        "recall_backlog_heads": len(recall_backlog),
        "boards": {name: len(rows) for name, rows in boards.items()},
        "created_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
    }

    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    MERGE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ROUNDS_DIR.mkdir(parents=True, exist_ok=True)

    round_name = args.round_name or f"task11_merge_{summary['created_at']}"
    raw_entities_path = MERGE_RESULTS_DIR / f"{round_name}_raw_entities.jsonl"
    forms_path = MERGE_RESULTS_DIR / f"{round_name}_entity_forms.jsonl"
    candidates_path = MERGE_RESULTS_DIR / f"{round_name}_candidate_pairs.jsonl"
    decisions_path = MERGE_RESULTS_DIR / f"{round_name}_merge_decisions.jsonl"
    clusters_path = MERGE_RESULTS_DIR / f"{round_name}_clusters.jsonl"
    review_samples_path = MERGE_RESULTS_DIR / f"{round_name}_review_samples.jsonl"
    backlog_path = MERGE_RESULTS_DIR / f"{round_name}_cluster_backlog.jsonl"
    recall_backlog_path = MERGE_RESULTS_DIR / f"{round_name}_recall_backlog.jsonl"
    summary_path = MERGE_RESULTS_DIR / f"{round_name}_summary.json"
    report_path = ROUNDS_DIR / f"{round_name}.md"
    board_paths = {
        name: MERGE_RESULTS_DIR / f"{round_name}_board_{name}.jsonl"
        for name in ["surface_variants", "inflection_variants", "explicit_aliases", "ambiguous_acronyms", "blocked_by_role", "recall_review", "risky_review"]
    }

    append_jsonl(raw_entities_path, mention_rows)
    append_jsonl(forms_path, forms)
    append_jsonl(candidates_path, candidate_rows)
    append_jsonl(decisions_path, candidate_rows)
    append_jsonl(clusters_path, clusters)
    append_jsonl(review_samples_path, review_samples)
    append_jsonl(backlog_path, cluster_backlog)
    append_jsonl(recall_backlog_path, recall_backlog)
    for name, path in board_paths.items():
        append_jsonl(path, boards.get(name, []))
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(
        render_report(round_name, summary, review_samples, [cluster for cluster in clusters if cluster["form_count"] >= 2][:20], boards, recall_backlog),
        encoding="utf-8",
    )

    print(f"Raw entities saved to: {raw_entities_path}")
    print(f"Entity forms saved to: {forms_path}")
    print(f"Candidate pairs saved to: {candidates_path}")
    print(f"Merge decisions saved to: {decisions_path}")
    print(f"Clusters saved to: {clusters_path}")
    print(f"Review samples saved to: {review_samples_path}")
    print(f"Cluster backlog saved to: {backlog_path}")
    print(f"Recall backlog saved to: {recall_backlog_path}")
    for name, path in board_paths.items():
        print(f"Board {name} saved to: {path}")
    print(f"Summary saved to: {summary_path}")
    print(f"Round report saved to: {report_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

from prompt_registry import DEFAULT_PROMPT_VERSION, PROMPT_REGISTRY


ROOT_DIR = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT_DIR / "corpus" / "per_book"
RESULTS_DIR = Path(__file__).resolve().parent / "results" / "batches"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run task 10 batch extraction in harness style, with resumable multi-book processing."
    )
    parser.add_argument(
        "--batch-name",
        required=True,
        help="Stable batch identifier. Reuse the same name to resume the same run.",
    )
    parser.add_argument(
        "--book",
        action="append",
        dest="books",
        help="Book filename fragment under corpus/per_book. Repeatable. Omit to use all available books.",
    )
    parser.add_argument(
        "--exclude-book",
        action="append",
        dest="exclude_books",
        help="Book filename fragment to exclude. Repeatable.",
    )
    parser.add_argument(
        "--max-books",
        type=int,
        default=None,
        help="Optional maximum number of selected books after filtering.",
    )
    parser.add_argument(
        "--chunk-limit-per-book",
        type=int,
        default=None,
        help="Optional maximum number of chunks per book after filtering.",
    )
    parser.add_argument(
        "--max-total-chunks",
        type=int,
        default=None,
        help="Optional maximum total chunks across the whole batch.",
    )
    parser.add_argument(
        "--min-char-count",
        type=int,
        default=250,
        help="Skip chunks shorter than this many characters.",
    )
    parser.add_argument(
        "--prompt-version",
        choices=sorted(PROMPT_REGISTRY.keys()),
        default=DEFAULT_PROMPT_VERSION,
        help="Prompt version to use for extraction.",
    )
    parser.add_argument(
        "--output-prefix",
        default="batch_extract",
        help="Prefix used before the batch name in results filenames.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("LLM_BASE_URL", "https://api.openai-proxy.org/v1"),
        help="OpenAI-compatible base URL. Can also be set with LLM_BASE_URL.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("LLM_MODEL", "deepseek-reasoner"),
        help="Model name. Can also be set with LLM_MODEL.",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"),
        help="API key. Prefer OPENAI_API_KEY or LLM_API_KEY env vars.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Optional delay between requests.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview selected books/chunks without making API calls.",
    )
    return parser.parse_args()


def resolve_books(book_queries, exclude_queries, max_books):
    files = sorted(CORPUS_DIR.glob("*.json"))
    if book_queries:
        selected = []
        for query in book_queries:
            matches = [path for path in files if query.lower() in path.name.lower()]
            if not matches:
                raise FileNotFoundError(f"No corpus file matched: {query}")
            selected.extend(matches)
    else:
        selected = files

    if exclude_queries:
        selected = [
            path for path in selected
            if not any(query.lower() in path.name.lower() for query in exclude_queries)
        ]

    unique = []
    seen = set()
    for path in selected:
        if path.name not in seen:
            unique.append(path)
            seen.add(path.name)

    if max_books is not None:
        unique = unique[:max_books]
    return unique


def load_chunks(book_path, min_char_count, chunk_limit_per_book):
    with book_path.open("r", encoding="utf-8") as handle:
        corpus = json.load(handle)

    selected = []
    for chunk in corpus:
        if chunk.get("char_count", 0) < min_char_count:
            continue
        selected.append(chunk)
        if chunk_limit_per_book is not None and len(selected) >= chunk_limit_per_book:
            break
    return selected


def build_prompt(chunk, prompt_template):
    return prompt_template.format(
        book_title=chunk["book_title"],
        chapter_title=chunk["chapter_title"],
        text=chunk["text"],
    )


def clean_response_text(content):
    content = content.strip()
    if content.startswith("```"):
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1].strip()
            if content.startswith("json"):
                content = content[4:].strip()
    return content


def validate_graph(payload):
    if not isinstance(payload, dict):
        raise ValueError("Response is not a JSON object.")

    entities = payload.get("entities")
    relations = payload.get("relations")
    if not isinstance(entities, list) or not isinstance(relations, list):
        raise ValueError("Response must contain list fields: entities and relations.")

    entity_ids = set()
    entity_names = set()
    for entity in entities:
        if not isinstance(entity, dict):
            raise ValueError("Each entity must be an object.")
        for field in ("id", "name", "type", "definition"):
            if field not in entity:
                raise ValueError(f"Entity missing field: {field}")
        entity_ids.add(entity["id"])
        normalized_name = entity["name"].strip().lower()
        if normalized_name in entity_names:
            raise ValueError(f"Duplicate entity name found: {entity['name']}")
        entity_names.add(normalized_name)

    for relation in relations:
        if not isinstance(relation, dict):
            raise ValueError("Each relation must be an object.")
        for field in ("source", "target", "relation"):
            if field not in relation:
                raise ValueError(f"Relation missing field: {field}")
        if relation["source"] not in entity_ids or relation["target"] not in entity_ids:
            raise ValueError("Relation references unknown entity id.")


def extract_graph(client, model, chunk, prompt_template):
    prompt = build_prompt(chunk, prompt_template)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = clean_response_text(response.choices[0].message.content)
    payload = json.loads(content)
    validate_graph(payload)
    return payload


def append_jsonl(path, record):
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_existing_successes(results_path):
    if not results_path.exists():
        return set()

    successes = set()
    for line in results_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("status") == "success":
            successes.add((row["book_file"], row["chunk_index"]))
    return successes


def write_json(path, payload):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def manifest_book_signature(manifest):
    return [
        (book["book_file"], book["selected_chunks"])
        for book in manifest.get("books", [])
    ]


def ensure_manifest_compatible(manifest_path, manifest):
    if not manifest_path.exists():
        return manifest

    existing_manifest = load_json(manifest_path)
    current_signature = manifest_book_signature(manifest)
    existing_signature = manifest_book_signature(existing_manifest)
    if current_signature != existing_signature:
        raise ValueError(
            "Existing batch manifest does not match the current book selection. "
            "Reuse the original --book/--max-books filters for this batch name, "
            "or choose a new --batch-name."
        )

    if existing_manifest.get("prompt_version") != manifest.get("prompt_version"):
        raise ValueError(
            "Existing batch manifest uses a different prompt version. "
            "Reuse the original --prompt-version for this batch name, "
            "or choose a new --batch-name."
        )

    manifest["created_at"] = existing_manifest.get("created_at", manifest["created_at"])
    return manifest


def main():
    args = parse_args()
    prompt_template = PROMPT_REGISTRY[args.prompt_version]
    book_paths = resolve_books(args.books, args.exclude_books, args.max_books)

    selected_by_book = {}
    total_candidate_chunks = 0
    for book_path in book_paths:
        chunks = load_chunks(book_path, args.min_char_count, args.chunk_limit_per_book)
        selected_by_book[book_path.name] = chunks
        total_candidate_chunks += len(chunks)

    if args.max_total_chunks is not None:
        remaining = args.max_total_chunks
        trimmed = {}
        for book_path in book_paths:
            chunks = selected_by_book[book_path.name]
            trimmed[book_path.name] = chunks[:remaining]
            remaining -= len(trimmed[book_path.name])
            if remaining <= 0:
                for tail_book in book_paths[book_paths.index(book_path) + 1:]:
                    trimmed[tail_book.name] = []
                break
        selected_by_book = trimmed
        total_candidate_chunks = sum(len(chunks) for chunks in selected_by_book.values())

    batch_stem = f"{args.output_prefix}_{args.batch_name}"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path = RESULTS_DIR / f"{batch_stem}.jsonl"
    summary_path = RESULTS_DIR / f"{batch_stem}_summary.json"
    manifest_path = RESULTS_DIR / f"{batch_stem}_manifest.json"

    manifest = {
        "batch_name": args.batch_name,
        "prompt_version": args.prompt_version,
        "model": args.model,
        "base_url": args.base_url,
        "books": [],
        "total_candidate_chunks": total_candidate_chunks,
        "created_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
    }
    for book_path in book_paths:
        manifest["books"].append(
            {
                "book_file": book_path.name,
                "selected_chunks": len(selected_by_book[book_path.name]),
            }
        )
    manifest = ensure_manifest_compatible(manifest_path, manifest)
    write_json(manifest_path, manifest)

    if args.dry_run:
        print(f"Batch: {args.batch_name}")
        print(f"Prompt version: {args.prompt_version}")
        print(f"Books selected: {len(book_paths)}")
        print(f"Candidate chunks: {total_candidate_chunks}")
        for book in manifest["books"]:
            print(f"- {book['book_file']} | chunks={book['selected_chunks']}")
        print(f"Manifest saved to: {manifest_path}")
        return

    if not args.api_key:
        raise ValueError("Missing API key. Set OPENAI_API_KEY or pass --api-key.")

    from openai import OpenAI

    client = OpenAI(base_url=args.base_url, api_key=args.api_key, timeout=args.timeout)

    existing_successes = load_existing_successes(results_path)
    summary = {
        "batch_name": args.batch_name,
        "prompt_version": args.prompt_version,
        "model": args.model,
        "base_url": args.base_url,
        "books_selected": len(book_paths),
        "candidate_chunks": total_candidate_chunks,
        "existing_successes_before_run": len(existing_successes),
        "processed_this_run": 0,
        "successes_this_run": 0,
        "failures_this_run": 0,
        "skipped_existing": 0,
        "started_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
    }

    for book_path in book_paths:
        chunks = selected_by_book[book_path.name]
        for chunk in chunks:
            key = (book_path.name, chunk["chunk_index"])
            if key in existing_successes:
                summary["skipped_existing"] += 1
                continue

            print(
                f"[{args.batch_name}] {book_path.name} | chunk {chunk['chunk_index']} | chars={chunk['char_count']}",
                flush=True,
            )
            record = {
                "batch_name": args.batch_name,
                "prompt_version": args.prompt_version,
                "book_file": book_path.name,
                "book_title": chunk["book_title"],
                "language": chunk["language"],
                "chapter_title": chunk["chapter_title"],
                "chunk_index": chunk["chunk_index"],
                "char_count": chunk["char_count"],
                "processed_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
            }
            summary["processed_this_run"] += 1

            try:
                record["result"] = extract_graph(client, args.model, chunk, prompt_template)
                record["status"] = "success"
                summary["successes_this_run"] += 1
            except Exception as exc:
                record["status"] = "error"
                record["error"] = str(exc)
                summary["failures_this_run"] += 1

            append_jsonl(results_path, record)
            write_json(summary_path, summary)

            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

    summary["finished_at"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary["results_file"] = str(results_path)
    summary["manifest_file"] = str(manifest_path)
    write_json(summary_path, summary)

    print(f"Results saved to: {results_path}")
    print(f"Summary saved to: {summary_path}")
    print(f"Manifest saved to: {manifest_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

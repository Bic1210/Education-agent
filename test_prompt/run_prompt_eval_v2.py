import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from prompt_registry import DEFAULT_PROMPT_VERSION, PROMPT_REGISTRY


ROOT_DIR = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT_DIR / "corpus" / "per_book"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a small-batch prompt v2 evaluation without touching the main pipeline."
    )
    parser.add_argument(
        "--book",
        action="append",
        dest="books",
        help="Book filename fragment under corpus/per_book. Repeatable. Default uses Book 04 and Book 09.",
    )
    parser.add_argument(
        "--chunk-indexes",
        help="Comma-separated chunk_index values to run, for example: 5,6,7,8",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=6,
        help="Maximum chunks per selected book after filtering.",
    )
    parser.add_argument(
        "--min-char-count",
        type=int,
        default=250,
        help="Skip chunks shorter than this many characters.",
    )
    parser.add_argument(
        "--output-prefix",
        default="prompt_eval",
        help="Prefix used for JSONL and summary output files under test_prompt/results.",
    )
    parser.add_argument(
        "--prompt-version",
        choices=sorted(PROMPT_REGISTRY.keys()),
        default=DEFAULT_PROMPT_VERSION,
        help="Prompt version to use for extraction.",
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
        "--dry-run",
        action="store_true",
        help="Only show which books/chunks would run. No API calls.",
    )
    return parser.parse_args()


def default_books():
    return [
        "04_Practical Statistics for Data Scientists",
        "09_可解释人工智能导论",
    ]


def resolve_books(book_queries):
    queries = book_queries or default_books()
    files = sorted(CORPUS_DIR.glob("*.json"))
    selected = []
    for query in queries:
        matches = [path for path in files if query.lower() in path.name.lower()]
        if not matches:
            raise FileNotFoundError(f"No corpus file matched: {query}")
        selected.extend(matches)

    unique = []
    seen = set()
    for path in selected:
        if path.name not in seen:
            unique.append(path)
            seen.add(path.name)
    return unique


def parse_chunk_indexes(raw_value):
    if not raw_value:
        return None
    values = set()
    for part in raw_value.split(","):
        part = part.strip()
        if part:
            values.add(int(part))
    return values or None


def load_chunks(book_path, chunk_indexes, max_chunks, min_char_count):
    with book_path.open("r", encoding="utf-8") as handle:
        corpus = json.load(handle)

    selected = []
    for chunk in corpus:
        if chunk.get("char_count", 0) < min_char_count:
            continue
        if chunk_indexes and chunk.get("chunk_index") not in chunk_indexes:
            continue
        selected.append(chunk)
        if len(selected) >= max_chunks:
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


def main():
    args = parse_args()
    chunk_indexes = parse_chunk_indexes(args.chunk_indexes)
    book_paths = resolve_books(args.books)
    selected_by_book = {
        book_path.name: load_chunks(book_path, chunk_indexes, args.max_chunks, args.min_char_count)
        for book_path in book_paths
    }

    if args.dry_run:
        print("Dry run only. No API calls will be made.")
        for book_name, chunks in selected_by_book.items():
            print(f"\n{book_name}")
            for chunk in chunks:
                print(
                    f"  chunk={chunk['chunk_index']} chars={chunk['char_count']} chapter={chunk['chapter_title']}"
                )
        return

    if not args.api_key:
        raise ValueError("Missing API key. Set OPENAI_API_KEY or pass --api-key.")

    from openai import OpenAI
    prompt_template = PROMPT_REGISTRY[args.prompt_version]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_path = RESULTS_DIR / f"{args.output_prefix}_{timestamp}.jsonl"
    summary_path = RESULTS_DIR / f"{args.output_prefix}_{timestamp}_summary.json"

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)

    summary = {
        "prompt_version": args.prompt_version,
        "model": args.model,
        "base_url": args.base_url,
        "books": [path.name for path in book_paths],
        "requested_chunk_indexes": sorted(chunk_indexes) if chunk_indexes else None,
        "max_chunks_per_book": args.max_chunks,
        "min_char_count": args.min_char_count,
        "started_at": timestamp,
        "total_chunks": 0,
        "successes": 0,
        "failures": 0,
    }

    for book_path in book_paths:
        chunks = selected_by_book[book_path.name]
        for chunk in chunks:
            summary["total_chunks"] += 1
            record = {
                "prompt_version": args.prompt_version,
                "book_file": book_path.name,
                "book_title": chunk["book_title"],
                "language": chunk["language"],
                "chapter_title": chunk["chapter_title"],
                "chunk_index": chunk["chunk_index"],
                "char_count": chunk["char_count"],
            }
            try:
                record["result"] = extract_graph(client, args.model, chunk, prompt_template)
                record["status"] = "success"
                summary["successes"] += 1
            except Exception as exc:
                record["status"] = "error"
                record["error"] = str(exc)
                summary["failures"] += 1
            append_jsonl(jsonl_path, record)

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    print(f"Results saved to: {jsonl_path}")
    print(f"Summary saved to: {summary_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

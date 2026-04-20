import argparse
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

from review_prompt_v1 import REVIEW_PROMPT_TEMPLATE, REVIEW_PROMPT_VERSION


ROOT_DIR = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT_DIR / "corpus" / "per_book"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
ROUNDS_DIR = Path(__file__).resolve().parent / "rounds"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Review extraction results with a second LLM assistant and save round artifacts."
    )
    parser.add_argument(
        "--results-file",
        required=True,
        help="Path to the extraction JSONL results file to review.",
    )
    parser.add_argument(
        "--round-name",
        default=None,
        help="Optional round label. Defaults to a timestamped name.",
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
        help="Only validate input records and print what would be reviewed.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of successful records to review.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Per-request timeout in seconds.",
    )
    return parser.parse_args()


def clean_response_text(content):
    content = content.strip()
    if content.startswith("```"):
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1].strip()
            if content.startswith("json"):
                content = content[4:].strip()
    return content


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_chunk_text(book_file, chunk_index):
    book_path = CORPUS_DIR / book_file
    with book_path.open("r", encoding="utf-8") as handle:
        corpus = json.load(handle)
    for chunk in corpus:
        if chunk.get("chunk_index") == chunk_index:
            return chunk
    raise ValueError(f"Chunk {chunk_index} not found in {book_file}")


def build_review_prompt(record, chunk):
    return REVIEW_PROMPT_TEMPLATE.format(
        book_title=record["book_title"],
        chapter_title=record["chapter_title"],
        text=chunk["text"],
        result_json=json.dumps(record["result"], ensure_ascii=False, indent=2),
    )


def validate_review_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Review response is not a JSON object.")

    required = [
        "review_verdict",
        "overall_comment",
        "issues",
        "should_revise_prompt",
        "prompt_revision_focus",
    ]
    for field in required:
        if field not in payload:
            raise ValueError(f"Review response missing field: {field}")

    if payload["review_verdict"] not in {"accept", "revise", "reject"}:
        raise ValueError("Invalid review_verdict.")
    if not isinstance(payload["issues"], list):
        raise ValueError("Review issues must be a list.")
    if not isinstance(payload["prompt_revision_focus"], list):
        raise ValueError("prompt_revision_focus must be a list.")

    for issue in payload["issues"]:
        if not isinstance(issue, dict):
            raise ValueError("Each issue must be an object.")
        for field in ("severity", "category", "target", "reason", "suggestion"):
            if field not in issue:
                raise ValueError(f"Issue missing field: {field}")


def review_record(client, model, record):
    chunk = load_chunk_text(record["book_file"], record["chunk_index"])
    prompt = build_review_prompt(record, chunk)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = clean_response_text(response.choices[0].message.content)
    payload = json.loads(content)
    validate_review_payload(payload)
    return payload


def append_jsonl(path, record):
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def render_round_report(round_name, extraction_file, review_file, summary, reviewed_rows):
    counts = Counter(row["review"]["review_verdict"] for row in reviewed_rows)
    categories = Counter()
    for row in reviewed_rows:
        for issue in row["review"]["issues"]:
            categories[issue["category"]] += 1

    lines = [
        f"# {round_name}",
        "",
        "## 基本信息",
        "",
        f"- 抽取结果文件：`{extraction_file}`",
        f"- 评审结果文件：`{review_file}`",
        f"- 抽取 Prompt 版本：`{summary['extraction_prompt_version']}`",
        f"- 评审 Prompt 版本：`{summary['review_prompt_version']}`",
        f"- 模型：`{summary['model']}`",
        f"- Base URL：`{summary['base_url']}`",
        f"- 评审条数：`{summary['reviewed_records']}`",
        "",
        "## 评审结论统计",
        "",
        f"- accept: {counts.get('accept', 0)}",
        f"- revise: {counts.get('revise', 0)}",
        f"- reject: {counts.get('reject', 0)}",
        "",
        "## 高频问题",
        "",
    ]

    for category, count in categories.most_common(8):
        lines.append(f"- {category}: {count}")

    lines.extend(["", "## 逐条摘要", ""])

    for row in reviewed_rows:
        review = row["review"]
        lines.append(
            f"- {row['book_title']} | chunk {row['chunk_index']} | {review['review_verdict']} | {review['overall_comment']}"
        )
        for issue in review["issues"][:3]:
            lines.append(
                f"  - [{issue['severity']}] {issue['category']} | {issue['target']} | {issue['reason']}"
            )

    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    results_path = Path(args.results_file).resolve()
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    rows = load_jsonl(results_path)
    success_rows = [row for row in rows if row.get("status") == "success"]
    if args.limit is not None:
        success_rows = success_rows[: args.limit]

    if args.dry_run:
        print(f"Would review {len(success_rows)} successful records from: {results_path}")
        for row in success_rows:
            print(f"- {row['book_title']} | chunk {row['chunk_index']} | prompt={row['prompt_version']}")
        return

    if not args.api_key:
        raise ValueError("Missing API key. Set OPENAI_API_KEY or pass --api-key.")

    from openai import OpenAI

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ROUNDS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    round_name = args.round_name or f"round_review_{timestamp}"
    review_jsonl_path = RESULTS_DIR / f"{round_name}_{REVIEW_PROMPT_VERSION}.jsonl"
    review_summary_path = RESULTS_DIR / f"{round_name}_{REVIEW_PROMPT_VERSION}_summary.json"
    round_report_path = ROUNDS_DIR / f"{round_name}.md"

    client = OpenAI(base_url=args.base_url, api_key=args.api_key, timeout=args.timeout)

    reviewed_rows = []
    summary = {
        "round_name": round_name,
        "review_prompt_version": REVIEW_PROMPT_VERSION,
        "model": args.model,
        "base_url": args.base_url,
        "extraction_results_file": str(results_path),
        "extraction_prompt_version": success_rows[0]["prompt_version"] if success_rows else None,
        "reviewed_records": 0,
        "failures": 0,
    }

    for row in success_rows:
        print(f"Reviewing: {row['book_title']} | chunk {row['chunk_index']}", flush=True)
        output_row = {
            "book_file": row["book_file"],
            "book_title": row["book_title"],
            "chapter_title": row["chapter_title"],
            "chunk_index": row["chunk_index"],
            "prompt_version": row["prompt_version"],
        }
        try:
            output_row["review"] = review_record(client, args.model, row)
            output_row["status"] = "success"
            summary["reviewed_records"] += 1
            reviewed_rows.append(output_row)
        except Exception as exc:
            output_row["status"] = "error"
            output_row["error"] = str(exc)
            summary["failures"] += 1
        append_jsonl(review_jsonl_path, output_row)

    with review_summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    round_report = render_round_report(
        round_name=round_name,
        extraction_file=results_path.name,
        review_file=review_jsonl_path.name,
        summary=summary,
        reviewed_rows=reviewed_rows,
    )
    round_report_path.write_text(round_report, encoding="utf-8")

    print(f"Review results saved to: {review_jsonl_path}")
    print(f"Review summary saved to: {review_summary_path}")
    print(f"Round report saved to: {round_report_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

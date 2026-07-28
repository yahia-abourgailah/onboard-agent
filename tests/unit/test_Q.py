#!/usr/bin/env python3
"""
test_raseeny.py — EVAL-1 multilingual eval runner for Raseeny.

Sends each question from eval_questions.json to the live Raseeny /chat
endpoint, then uses an LLM judge (OpenAI or Anthropic — whichever key you
have) to score the response against the expected outcome / source / answer,
and writes a results report.

Usage:
    export LANGSMITH_API_KEY="your-raseeny-auth-key"
    export OPENAI_API_KEY="your-openai-api-key"
    python3 test_raseeny.py

    # optional flags
    python3 test_raseeny.py --base-url http://127.0.0.1:8000 \
        --language Arabic --category Policy --limit 5 \
        --no-judge --output results.csv
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, cast

import requests
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

try:
    from dotenv import find_dotenv, load_dotenv

    _dotenv_path = find_dotenv(usecwd=True)
    if _dotenv_path:
        load_dotenv(_dotenv_path)
        print(f"[info] Loaded environment variables from {_dotenv_path}", file=sys.stderr)
    else:
        print(
            "[info] No .env file found (searched from current directory upward) — "
            "using shell environment variables only.",
            file=sys.stderr,
        )
except ImportError:
    print(
        "[warn] python-dotenv not installed — .env files won't be auto-loaded. "
        "Run: pip install python-dotenv  (or keep setting env vars manually with $env:)",
        file=sys.stderr,
    )

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_QUESTIONS_FILE = SCRIPT_DIR / "eval_questions.json"

ANTHROPIC_JUDGE_MODEL = "claude-sonnet-4-6"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

OPENAI_JUDGE_MODEL = "gpt-4o-mini"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

RASEENY_KEY_ENV_CANDIDATES = [
    "API_TOKEN",
    "RASEENY_API_KEY",
    "LANGSMITH_API_KEY",
    "INTERNAL_API_KEYS",
    "AUTH_TOKEN",
]


def _find_raseeny_key() -> tuple[str | None, str | None]:
    """Look for the Raseeny auth token under a few common env var names,
    since every project names it differently. First match wins."""
    for name in RASEENY_KEY_ENV_CANDIDATES:
        val = os.environ.get(name)
        if val:
            return val, name
    return None, None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the EVAL-1 eval set against Raseeny.")
    p.add_argument(
        "--base-url",
        default=os.environ.get("RASEENY_BASE_URL", "http://127.0.0.1:8000"),
        help="Base URL of the running Raseeny API (default: %(default)s)",
    )
    p.add_argument("--chat-path", default="/chat", help="Chat endpoint path (default: %(default)s)")
    p.add_argument(
        "--reset-path", default="/new-chat", help="Session reset endpoint (default: %(default)s)"
    )
    _default_key, _default_key_source = _find_raseeny_key()
    p.add_argument(
        "--api-key",
        default=_default_key,
        help="Bearer token for Raseeny auth. Auto-detected from env vars: "
        + ", ".join(RASEENY_KEY_ENV_CANDIDATES)
        + " (first match wins), "
        "or pass --api-key / --api-key-env explicitly.",
    )
    p.add_argument(
        "--api-key-env",
        default=None,
        help="Explicit env var name to read the Raseeny auth token from, "
        "if it's not one of: " + ", ".join(RASEENY_KEY_ENV_CANDIDATES),
    )
    p.add_argument(
        "--message-field",
        default="prompt",
        help=(
            "JSON field name the /chat endpoint expects for the user message (default: %(default)s)"
        ),
    )
    p.add_argument(
        "--questions-file",
        default=str(DEFAULT_QUESTIONS_FILE),
        help="Path to eval_questions.json (default: %(default)s)",
    )
    p.add_argument(
        "--language",
        default=None,
        help="Only run questions for this language (English/Arabic/Franco-Arabic)",
    )
    p.add_argument(
        "--category",
        default=None,
        help="Only run questions for this category (Policy/Who-to-ask/Out-of-scope)",
    )
    p.add_argument(
        "--limit", type=int, default=None, help="Only run the first N matching questions"
    )
    p.add_argument(
        "--no-judge", action="store_true", help="Skip LLM auto-grading; just log raw responses"
    )
    p.add_argument(
        "--judge-provider",
        choices=["openai", "anthropic"],
        default=None,
        help="Which LLM to use as judge. Default: auto-detect from whichever API key is set "
        "(OPENAI_API_KEY or ANTHROPIC_API_KEY), preferring OpenAI if both are set.",
    )
    p.add_argument(
        "--openai-api-key",
        default=os.environ.get("OPENAI_API_KEY"),
        help="API key for the LLM judge if using OpenAI (or set OPENAI_API_KEY env var)",
    )
    p.add_argument(
        "--anthropic-api-key",
        default=os.environ.get("ANTHROPIC_API_KEY"),
        help="API key for the LLM judge if using Anthropic (or set ANTHROPIC_API_KEY env var)",
    )
    p.add_argument(
        "--output", default="eval_results.csv", help="Output CSV path (default: %(default)s)"
    )
    p.add_argument(
        "--xlsx-output",
        default=None,
        help="Also write a formatted, color-coded .xlsx report to this path "
        "(default: same name as --output with .xlsx extension)",
    )
    p.add_argument(
        "--no-xlsx", action="store_true", help="Skip the formatted xlsx report, CSV only"
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds (default: %(default)s)",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to sleep between questions (default: %(default)s)",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help=(
            "Print raw HTTP status + response body for every question "
            "(for diagnosing 401/422/schema issues)"
        ),
    )
    return p.parse_args()


# --------------------------------------------------------------------------
# Raseeny calls
# --------------------------------------------------------------------------


def build_session(api_key: str) -> requests.Session:
    s = requests.Session()
    if api_key:
        s.headers.update({"Authorization": f"Bearer {api_key}"})
    s.headers.update({"Content-Type": "application/json"})
    return s


def reset_thread(session: requests.Session, base_url: str, reset_path: str, timeout: float) -> None:
    """Call POST /new-chat so each question starts a fresh conversation thread.
    Non-fatal if the endpoint doesn't exist — we just log a warning once."""
    try:
        session.post(base_url + reset_path, timeout=timeout)
    except requests.RequestException as e:
        print(f"  [warn] could not reset session via {reset_path}: {e}", file=sys.stderr)


def ask_raseeny(
    session: requests.Session,
    base_url: str,
    chat_path: str,
    message_field: str,
    question: str,
    timeout: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {message_field: question}
    started = time.time()
    try:
        resp = session.post(base_url + chat_path, json=payload, timeout=timeout)
        latency_ms = round((time.time() - started) * 1000, 1)
        status_code = resp.status_code
        body_text = resp.text
        resp.raise_for_status()
        data = resp.json()
        # Try common response shapes; fall back to the raw JSON as a string.
        answer = (
            data.get("answer")
            or data.get("response")
            or data.get("message")
            or data.get("reply")
            or json.dumps(data, ensure_ascii=False)
        )
        return {
            "ok": True,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "raw": data,
            "raw_text": body_text,
            "answer": answer,
        }
    except requests.RequestException as e:
        latency_ms = round((time.time() - started) * 1000, 1)
        err_resp = getattr(e, "response", None)
        return {
            "ok": False,
            "status_code": err_resp.status_code if err_resp is not None else None,
            "latency_ms": latency_ms,
            "raw": None,
            "raw_text": err_resp.text if err_resp is not None else None,
            "answer": None,
            "error": str(e),
        }


# --------------------------------------------------------------------------
# LLM judge
# --------------------------------------------------------------------------

JUDGE_SYSTEM_PROMPT = (
    "You are grading responses from an internal HR/IT onboarding chatbot "
    "called Raseeny.\n"
    "You will be given a question, the expected outcome type, the expected "
    "source/owner, a reference answer,\n"
    "and the chatbot's actual response. The chatbot may answer in English, "
    "Arabic, or Franco-Arabic (Arabic\n"
    "written in Latin letters/numbers) — grade the CONTENT, not the "
    "script/language used.\n"
    "\n"
    "Grading rules:\n"
    '- If Expected Outcome is "Answer + Source": PASS if the actual response '
    "contains the correct factual\n"
    "  answer (matching the reference answer's key facts/numbers) AND references "
    "or is clearly grounded in\n"
    "  the expected source. PARTIAL if the facts are mostly right but the source "
    "is missing/wrong, or vice versa.\n"
    "  FAIL if the facts are wrong, missing, or fabricated (hallucinated).\n"
    '- If Expected Outcome is "Escalate": PASS if the chatbot declines to answer '
    "directly and appropriately\n"
    "  directs the user to a human/team/process instead of inventing an answer. "
    "FAIL if it fabricates an answer\n"
    "  it has no authority/knowledge basis for.\n"
    "\n"
    "Respond ONLY with a JSON object, no markdown fences, no preamble:\n"
    '{"verdict": "PASS" | "PARTIAL" | "FAIL", "reasoning": "one or two sentence '
    'explanation"}\n'
)


def _judge_user_content(row: dict[str, Any], actual_answer: str) -> str:
    return (
        f"Question ({row.get('Language')}): {row.get('Question')}\n"
        f"Expected Outcome: {row.get('Expected Outcome')}\n"
        f"Expected Source/Owner: {row.get('Expected Source / Owner')}\n"
        f"Reference Answer: {row.get('Expected Answer / Notes')}\n\n"
        f"Actual chatbot response: {actual_answer}"
    )


def _parse_verdict_json(text: str) -> dict[str, str]:
    text = text.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(text)
    return {"verdict": parsed.get("verdict", "UNKNOWN"), "reasoning": parsed.get("reasoning", "")}


def judge_with_anthropic(api_key: str, row: dict[str, Any], actual_answer: str) -> dict[str, str]:
    body: dict[str, Any] = {
        "model": ANTHROPIC_JUDGE_MODEL,
        "max_tokens": 300,
        "system": JUDGE_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": _judge_user_content(row, actual_answer)}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    resp = requests.post(ANTHROPIC_URL, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    text = "".join(
        b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
    ).strip()
    return _parse_verdict_json(text)


def judge_with_openai(api_key: str, row: dict[str, Any], actual_answer: str) -> dict[str, str]:
    body: dict[str, Any] = {
        "model": OPENAI_JUDGE_MODEL,
        "max_tokens": 300,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": _judge_user_content(row, actual_answer)},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    resp = requests.post(OPENAI_URL, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"].strip()
    return _parse_verdict_json(text)


def judge_response(
    provider: str | None,
    api_key: str | None,
    row: dict[str, Any],
    actual_answer: str,
    request_failed: bool,
) -> dict[str, str]:
    if request_failed:
        return {"verdict": "FAIL", "reasoning": "Request to Raseeny failed — no response to grade."}
    if not api_key:
        return {"verdict": "UNGRADED", "reasoning": "No judge API key available."}
    try:
        if provider == "openai":
            return judge_with_openai(api_key, row, actual_answer)
        elif provider == "anthropic":
            return judge_with_anthropic(api_key, row, actual_answer)
        else:
            return {"verdict": "UNGRADED", "reasoning": f"Unknown judge provider: {provider}"}
    except Exception as e:
        return {"verdict": "UNGRADED", "reasoning": f"Judge call failed: {e}"}


VERDICT_FILLS = {
    "PASS": PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"),
    "PARTIAL": PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid"),
    "FAIL": PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"),
    "UNGRADED": PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
    "UNKNOWN": PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
}
VERDICT_FONT_COLORS = {
    "PASS": "006100",
    "PARTIAL": "9C6500",
    "FAIL": "9C0006",
    "UNGRADED": "595959",
    "UNKNOWN": "595959",
}


def write_xlsx_report(results: list[dict[str, Any]], path: str) -> None:
    """Write a color-coded, filterable xlsx report grouped by Language then Category.
    One sheet with everything (sorted + filterable) plus a Summary sheet with counts."""
    ordered = sorted(
        results,
        key=lambda r: (r["Language"] or "", r["Category"] or "", r["ID"] or 0),
    )

    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Results"

    headers = [
        "ID",
        "Language",
        "Category",
        "Question",
        "Expected Outcome",
        "Expected Source",
        "Expected Answer",
        "Actual Answer",
        "Verdict",
        "Judge Reasoning",
        "HTTP Status",
        "Latency (ms)",
        "Request OK",
    ]
    header_font = Font(name="Arial", bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="404040", end_color="404040", fill_type="solid")
    ws.append(headers)
    for col_idx, _ in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center")

    wrap = Alignment(wrap_text=True, vertical="top")
    body_font = Font(name="Arial")

    for row in ordered:
        ws.append(
            [
                row["ID"],
                row["Language"],
                row["Category"],
                row["Question"],
                row["Expected Outcome"],
                row["Expected Source"],
                row["Expected Answer"],
                row["Actual Answer"],
                row["Verdict"],
                row["Judge Reasoning"],
                row["HTTP Status"],
                row["Latency (ms)"],
                row["Request OK"],
            ]
        )
        excel_row = ws.max_row
        verdict = row["Verdict"] or "UNGRADED"
        fill = VERDICT_FILLS.get(verdict, VERDICT_FILLS["UNGRADED"])
        font_color = VERDICT_FONT_COLORS.get(verdict, VERDICT_FONT_COLORS["UNGRADED"])
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=excel_row, column=col_idx)
            cell.font = body_font
            cell.alignment = wrap
        verdict_col = headers.index("Verdict") + 1
        vcell = ws.cell(row=excel_row, column=verdict_col)
        vcell.fill = fill
        vcell.font = Font(name="Arial", bold=True, color=font_color)

    widths = {
        "ID": 6,
        "Language": 14,
        "Category": 13,
        "Question": 45,
        "Expected Outcome": 14,
        "Expected Source": 28,
        "Expected Answer": 45,
        "Actual Answer": 45,
        "Verdict": 11,
        "Judge Reasoning": 35,
        "HTTP Status": 11,
        "Latency (ms)": 12,
        "Request OK": 11,
    }
    for col_idx, h in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = widths.get(h, 15)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"
    ws.row_dimensions[1].height = 20

    # Summary sheet
    ws2 = wb.create_sheet("Summary")
    ws2.append(["EVAL-1 — Run Summary"])
    ws2["A1"].font = Font(name="Arial", bold=True, size=14)
    ws2.append([])
    ws2.append(["Total questions", len(ordered)])

    def counts_by(key: str) -> dict[Any, dict[str, int]]:
        buckets: dict[Any, dict[str, int]] = {}
        for rec in ordered:
            buckets.setdefault(rec[key], {})
            v = rec["Verdict"] or "UNGRADED"
            buckets[rec[key]][v] = buckets[rec[key]].get(v, 0) + 1
        return buckets

    verdict_totals: dict[str, int] = {}
    for rec in ordered:
        v = rec["Verdict"] or "UNGRADED"
        verdict_totals[v] = verdict_totals.get(v, 0) + 1

    ws2.append([])
    ws2.append(["Overall verdict breakdown"])
    ws2["A6"].font = Font(name="Arial", bold=True)
    for v, c in sorted(verdict_totals.items()):
        ws2.append([v, c])
        cell = ws2.cell(row=ws2.max_row, column=1)
        cell.fill = VERDICT_FILLS.get(v, VERDICT_FILLS["UNGRADED"])

    for label, key in [("By language", "Language"), ("By category", "Category")]:
        ws2.append([])
        ws2.append([label])
        ws2.cell(row=ws2.max_row, column=1).font = Font(name="Arial", bold=True)
        for k, verdicts in counts_by(key).items():
            parts = ", ".join(f"{v}: {c}" for v, c in sorted(verdicts.items()))
            ws2.append([k, parts])

    ws2.column_dimensions["A"].width = 22
    ws2.column_dimensions["B"].width = 45

    wb.save(path)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def load_questions(
    path: str, language: str | None, category: str | None, limit: int | None
) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        rows = cast(list[dict[str, Any]], json.load(f))
    if language:
        rows = [r for r in rows if r.get("Language", "").lower() == language.lower()]
    if category:
        rows = [r for r in rows if r.get("Category", "").lower() == category.lower()]
    if limit:
        rows = rows[:limit]
    return rows


def main() -> None:
    args = parse_args()

    if args.api_key_env:
        override = os.environ.get(args.api_key_env)
        if override:
            args.api_key = override
        else:
            print(
                f"[warn] --api-key-env was set to '{args.api_key_env}' "
                "but that env var is empty/unset.",
                file=sys.stderr,
            )

    if not args.api_key:
        print(
            "[warn] No Raseeny API key found. Checked env vars: "
            f"{', '.join(RASEENY_KEY_ENV_CANDIDATES)}. "
            "Set one of those, or pass --api-key <token> / --api-key-env <YOUR_VAR_NAME>. "
            "Requests will be sent without auth and will likely get a 401.",
            file=sys.stderr,
        )

    use_judge = not args.no_judge
    judge_provider = args.judge_provider
    judge_api_key = None
    if use_judge:
        if judge_provider is None:
            if args.openai_api_key:
                judge_provider = "openai"
            elif args.anthropic_api_key:
                judge_provider = "anthropic"
        if judge_provider == "openai":
            judge_api_key = args.openai_api_key
        elif judge_provider == "anthropic":
            judge_api_key = args.anthropic_api_key

        if not judge_provider or not judge_api_key:
            print(
                "[warn] No OPENAI_API_KEY or ANTHROPIC_API_KEY set — disabling auto-grading, "
                "will log raw responses only.",
                file=sys.stderr,
            )
            use_judge = False

    rows = load_questions(args.questions_file, args.language, args.category, args.limit)
    if not rows:
        print("No questions matched the given filters. Exiting.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(rows)} questions from {args.questions_file}")
    print(f"Target: {args.base_url}{args.chat_path}")
    grading_status = f"ON ({judge_provider})" if use_judge and judge_provider else "OFF"
    print(f"Auto-grading: {grading_status}\n")

    session = build_session(args.api_key)

    fieldnames: list[str] = [
        "ID",
        "Language",
        "Category",
        "Question",
        "Expected Outcome",
        "Expected Source",
        "Expected Answer",
        "Actual Answer",
        "HTTP Status",
        "Latency (ms)",
        "Request OK",
        "Verdict",
        "Judge Reasoning",
    ]
    results: list[dict[str, Any]] = []
    verdict_counts: dict[str, int] = {}

    for i, row in enumerate(rows, 1):
        qid = row.get("ID")
        lang = row.get("Language")
        cat = row.get("Category")
        question: str = row.get("Question") or ""
        q_preview = question[:70] + ("..." if len(question) > 70 else "")
        print(f"[{i}/{len(rows)}] #{qid} ({lang}/{cat}): {q_preview}")

        reset_thread(session, args.base_url, args.reset_path, args.timeout)
        result = ask_raseeny(
            session, args.base_url, args.chat_path, args.message_field, question, args.timeout
        )

        if args.debug:
            print(f"    [debug] status={result.get('status_code')} ok={result['ok']}")
            print(f"    [debug] raw body: {result.get('raw_text')}")

        actual = result.get("answer") or f"[ERROR] {result.get('error', 'unknown error')}"

        if use_judge:
            verdict_info = judge_response(
                judge_provider, judge_api_key, row, actual, not result["ok"]
            )
        else:
            verdict_info = {"verdict": "UNGRADED", "reasoning": ""}

        verdict = verdict_info["verdict"]
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        print(f"    -> {verdict}  ({result['latency_ms']} ms)")

        results.append(
            {
                "ID": qid,
                "Language": lang,
                "Category": cat,
                "Question": question,
                "Expected Outcome": row.get("Expected Outcome"),
                "Expected Source": row.get("Expected Source / Owner"),
                "Expected Answer": row.get("Expected Answer / Notes"),
                "Actual Answer": actual,
                "HTTP Status": result.get("status_code"),
                "Latency (ms)": result.get("latency_ms"),
                "Request OK": result["ok"],
                "Verdict": verdict,
                "Judge Reasoning": verdict_info["reasoning"],
            }
        )

        if args.delay:
            time.sleep(args.delay)

    # Write CSV
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Write formatted xlsx report (sorted by Language/Category, color-coded verdicts,
    # frozen header, autofilter, Summary tab)
    xlsx_path = None
    if not args.no_xlsx:
        xlsx_path = args.xlsx_output or str(Path(args.output).with_suffix(".xlsx"))
        write_xlsx_report(results, xlsx_path)

    # Summary
    print("\n" + "=" * 60)
    print(f"DONE — {len(results)} questions run. Results written to {args.output}")
    if xlsx_path:
        print(f"Formatted report written to {xlsx_path}")
    print("=" * 60)
    print("\nVerdict breakdown:")
    for v, c in sorted(verdict_counts.items()):
        print(f"  {v:10s} {c}")

    def breakdown(key: str) -> dict[Any, dict[str, int]]:
        buckets: dict[Any, dict[str, int]] = {}
        for r in results:
            buckets.setdefault(r[key], {}).setdefault(r["Verdict"], 0)
            buckets[r[key]][r["Verdict"]] += 1
        return buckets

    for label, key in [("By language", "Language"), ("By category", "Category")]:
        print(f"\n{label}:")
        for k, breakdown_counts in breakdown(key).items():
            print(f"  {k:15s} {breakdown_counts}")

    failed = [r for r in results if r["Verdict"] == "FAIL"]
    if failed:
        print(f"\n{len(failed)} FAILs:")
        for r in failed:
            print(f"  #{r['ID']} ({r['Language']}/{r['Category']}): {r['Question'][:60]}")


if __name__ == "__main__":
    main()

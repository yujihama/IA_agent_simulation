from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ia_sim.storage import write_json


BRANCHING_RUN_FILES = [
    "run_manifest.json",
    "branching_calls.jsonl",
    "branching_proposals.jsonl",
    "branching_grounding.jsonl",
    "llm_action_decisions.jsonl",
    "events.jsonl",
    "detector_annotations.jsonl",
    "findings.json",
    "branching_summary.json",
    "world_summaries.json",
    "world_tree.json",
    "branching_report.md",
    "residual_risk_report.md",
]
BRANCHING_COMPARISON_FILES = [
    "branching_variant_comparison.json",
    "branching_variant_comparison_report.md",
]

SENSITIVE_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "sk-REDACTED"),
    (re.compile(r"gh[opsru]_[A-Za-z0-9_]{20,}"), "gh-REDACTED"),
    (re.compile(r"(Authorization:\s*Bearer\s+)[A-Za-z0-9_\-.]+", re.IGNORECASE), r"\1REDACTED"),
    (re.compile(r"(OPENAI_API_KEY\s*=\s*)[^\s\"']+", re.IGNORECASE), r"\1REDACTED"),
    (re.compile(r"[A-Za-z]:\\\\Users\\\\[^\"\\]*(?:\\\\[^\"\\]*)*"), "<redacted-local-path>"),
    (re.compile(r"[A-Za-z]:\\Users\\[^\"'\r\n]+"), "<redacted-local-path>"),
]


def export_redacted_branching_evidence(
    *,
    source_root: Path,
    output_dir: Path,
    run_id: str = "RUN-S002-BRANCHING-BASELINE",
    comparison_id: str = "CMP-S002-BRANCHING-BASELINE-VARIANTS",
) -> dict[str, Any]:
    run_source = source_root / run_id
    comparison_source = source_root / "comparisons" / comparison_id
    run_target = output_dir / run_id
    comparison_target = output_dir / "comparisons" / comparison_id
    copied_files: list[str] = []
    missing_files: list[str] = []

    for file_name in BRANCHING_RUN_FILES:
        source_path = run_source / file_name
        target_path = run_target / file_name
        if _copy_redacted_file(source_path, target_path):
            copied_files.append(str(target_path.relative_to(output_dir)))
        else:
            missing_files.append(str(source_path.relative_to(source_root)))

    for file_name in BRANCHING_COMPARISON_FILES:
        source_path = comparison_source / file_name
        target_path = comparison_target / file_name
        if _copy_redacted_file(source_path, target_path):
            copied_files.append(str(target_path.relative_to(output_dir)))
        else:
            missing_files.append(str(source_path.relative_to(source_root)))

    redaction_policy = {
        "mode": "pattern_redaction",
        "raw_prompts_preserved": True,
        "raw_responses_preserved": True,
        "redacted_patterns": [
            "OpenAI API keys matching sk-*",
            "GitHub tokens matching gh*_",
            "Authorization bearer tokens",
            "OPENAI_API_KEY assignment values",
            "local Windows user paths under C:\\Users\\*",
        ],
        "not_redacted": [
            "synthetic purchase need data",
            "LLM prompt text",
            "LLM raw response text",
            "parsed JSON",
            "validation status and retry metadata",
        ],
    }
    manifest = {
        "source_root": "<redacted-local-source-root>",
        "source_root_name": source_root.name,
        "run_id": run_id,
        "comparison_id": comparison_id,
        "copied_files": copied_files,
        "missing_files": missing_files,
        "redaction_policy": "redaction_policy.json",
        "review_note": (
            "These artifacts are redacted PoC evidence. They preserve prompt/response and parsed outputs "
            "for review while removing token-like secrets by pattern."
        ),
    }
    write_json(output_dir / "redaction_policy.json", redaction_policy)
    write_json(output_dir / "evidence_manifest.json", manifest)
    return manifest


def _copy_redacted_file(source_path: Path, target_path: Path) -> bool:
    if not source_path.exists():
        return False
    text = source_path.read_text(encoding="utf-8")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(_redact_text(text), encoding="utf-8")
    return True


def _redact_text(text: str) -> str:
    redacted = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted

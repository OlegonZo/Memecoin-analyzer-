"""Command-line interface for evaluating a local synthetic snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .models import TokenSnapshot
from .scoring import Evaluation, evaluate_snapshot


def load_snapshot(path: Path) -> TokenSnapshot:
    with path.open("r", encoding="utf-8") as source:
        raw = json.load(source)
    if not isinstance(raw, dict):
        raise ValueError("snapshot JSON must contain one object")
    return TokenSnapshot.from_mapping(raw)


def render_text(evaluation: Evaluation) -> str:
    rows = [
        f"Token: {evaluation.symbol}",
        f"Decision: {evaluation.decision}",
        f"Accumulation score: {evaluation.accumulation_score:.2f}/100",
        f"Eligible wallets: {evaluation.eligible_wallet_count}",
        f"Dust/negative observations excluded: {evaluation.excluded_wallet_count}",
        f"Quality-weighted net buying: ${evaluation.weighted_buy_usd:,.2f}",
        "",
        "Risk and quality gates:",
    ]
    rows.extend(
        f"  [{'PASS' if gate.passed else 'FAIL'}] {gate.name}: "
        f"{gate.observed} (required {gate.requirement})"
        for gate in evaluation.gates
    )
    rows.extend(("", "Explanation:"))
    rows.extend(f"  - {line}" for line in evaluation.explanation)
    return "\n".join(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate a synthetic wallet-accumulation snapshot."
    )
    parser.add_argument("snapshot", type=Path, help="Path to a local JSON snapshot")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print the full explainable result as JSON",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    evaluation = evaluate_snapshot(load_snapshot(args.snapshot))
    if args.as_json:
        print(json.dumps(evaluation.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(render_text(evaluation))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



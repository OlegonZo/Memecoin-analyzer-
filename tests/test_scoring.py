from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from memecoin_analyzer_demo.cli import load_snapshot, render_text
from memecoin_analyzer_demo.models import (
    EvaluationPolicy,
    TokenSnapshot,
    WalletObservation,
)
from memecoin_analyzer_demo.scoring import evaluate_snapshot


def good_snapshot(**overrides: object) -> TokenSnapshot:
    values: dict[str, object] = {
        "symbol": "SYNTH",
        "liquidity_usd": 180_000,
        "volume_24h_usd": 350_000,
        "top_10_holder_ratio": 0.40,
        "mint_authority_enabled": False,
        "freeze_authority_enabled": False,
        "wallets": (
            WalletObservation("SYNTH_A", 9_000, 0.9),
            WalletObservation("SYNTH_B", 7_000, 0.8),
            WalletObservation("SYNTH_C", 5_000, 0.7),
            WalletObservation("SYNTH_D", 3_000, 0.6),
        ),
    }
    values.update(overrides)
    return TokenSnapshot(**values)


class EvaluationTests(unittest.TestCase):
    def test_healthy_synthetic_snapshot_is_watch(self) -> None:
        result = evaluate_snapshot(good_snapshot())

        self.assertEqual("WATCH", result.decision)
        self.assertTrue(result.passed_all_gates)
        self.assertGreaterEqual(result.accumulation_score, 60)
        self.assertEqual(4, result.eligible_wallet_count)

    def test_dust_and_negative_activity_are_excluded(self) -> None:
        snapshot = good_snapshot(
            wallets=(
                WalletObservation("SYNTH_A", 1_000, 1.0),
                WalletObservation("SYNTH_DUST", 499.99, 1.0),
                WalletObservation("SYNTH_SELLER", -2_000, 1.0),
            )
        )
        policy = EvaluationPolicy(
            min_distinct_wallets=1,
            target_distinct_wallets=1,
            target_weighted_buy_usd=1_000,
            min_accumulation_score=0,
        )

        result = evaluate_snapshot(snapshot, policy)

        self.assertEqual(1, result.eligible_wallet_count)
        self.assertEqual(2, result.excluded_wallet_count)
        self.assertEqual(1_000, result.weighted_buy_usd)
        self.assertEqual(("SYNTH_A",), tuple(row.wallet_id for row in result.contributions))

    def test_risk_authority_blocks_decision_with_explanation(self) -> None:
        result = evaluate_snapshot(good_snapshot(mint_authority_enabled=True))

        self.assertEqual("REJECT", result.decision)
        self.assertFalse(result.passed_all_gates)
        self.assertTrue(any("mint_authority failed" in row for row in result.explanation))

    def test_holder_concentration_gate_is_inclusive_at_limit(self) -> None:
        accepted = evaluate_snapshot(good_snapshot(top_10_holder_ratio=0.65))
        rejected = evaluate_snapshot(good_snapshot(top_10_holder_ratio=0.651))

        accepted_gate = next(g for g in accepted.gates if g.name == "holder_concentration")
        rejected_gate = next(g for g in rejected.gates if g.name == "holder_concentration")
        self.assertTrue(accepted_gate.passed)
        self.assertFalse(rejected_gate.passed)

    def test_invalid_quality_is_rejected_at_model_boundary(self) -> None:
        with self.assertRaisesRegex(ValueError, "quality"):
            WalletObservation("SYNTH_INVALID", 1_000, 1.01)

        with self.assertRaisesRegex(ValueError, "net_buy_usd"):
            WalletObservation("SYNTH_INVALID", float("nan"), 0.5)

    def test_duplicate_synthetic_wallets_are_rejected(self) -> None:
        duplicate = (
            WalletObservation("SYNTH_DUP", 1_000, 0.5),
            WalletObservation("SYNTH_DUP", 2_000, 0.6),
        )
        with self.assertRaisesRegex(ValueError, "unique"):
            good_snapshot(wallets=duplicate)

    def test_repository_example_loads_and_renders(self) -> None:
        snapshot = load_snapshot(PROJECT_ROOT / "examples" / "synthetic_snapshot.json")
        result = evaluate_snapshot(snapshot)
        rendered = render_text(result)

        self.assertEqual("WATCH", result.decision)
        self.assertIn("Decision: WATCH", rendered)
        self.assertIn("not a trade instruction", rendered)
        self.assertTrue(all(row.wallet_id.startswith("SYNTH_") for row in snapshot.wallets))

    def test_json_result_is_serializable(self) -> None:
        result = evaluate_snapshot(good_snapshot())
        encoded = json.dumps(result.to_dict())
        self.assertIn('"decision": "WATCH"', encoded)


if __name__ == "__main__":
    unittest.main()


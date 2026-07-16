"""Explainable wallet-accumulation scoring for synthetic snapshots.

The public formula is intentionally simple. It demonstrates engineering
structure and explainability without exposing production discovery logic or
calibrated thresholds.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .models import EvaluationPolicy, TokenSnapshot, WalletObservation


@dataclass(frozen=True, slots=True)
class WalletContribution:
    wallet_id: str
    net_buy_usd: float
    quality: float
    weight: float
    weighted_buy_usd: float


@dataclass(frozen=True, slots=True)
class GateResult:
    name: str
    passed: bool
    observed: str
    requirement: str


@dataclass(frozen=True, slots=True)
class Evaluation:
    symbol: str
    decision: str
    accumulation_score: float
    eligible_wallet_count: int
    excluded_wallet_count: int
    weighted_buy_usd: float
    contributions: tuple[WalletContribution, ...]
    gates: tuple[GateResult, ...]
    explanation: tuple[str, ...]

    @property
    def passed_all_gates(self) -> bool:
        return all(gate.passed for gate in self.gates)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _wallet_weight(wallet: WalletObservation) -> float:
    """Map quality from [0, 1] to a conservative public weight [0.5, 1]."""

    return 0.5 + (0.5 * wallet.quality)


def _gate(name: str, passed: bool, observed: str, requirement: str) -> GateResult:
    return GateResult(
        name=name,
        passed=passed,
        observed=observed,
        requirement=requirement,
    )


def evaluate_snapshot(
    snapshot: TokenSnapshot,
    policy: EvaluationPolicy | None = None,
) -> Evaluation:
    """Evaluate a snapshot and return both the decision and its full rationale."""

    policy = policy or EvaluationPolicy()

    eligible = tuple(
        wallet
        for wallet in snapshot.wallets
        if wallet.net_buy_usd >= policy.dust_threshold_usd
    )
    contributions = tuple(
        WalletContribution(
            wallet_id=wallet.wallet_id,
            net_buy_usd=round(wallet.net_buy_usd, 2),
            quality=round(wallet.quality, 4),
            weight=round(_wallet_weight(wallet), 4),
            weighted_buy_usd=round(wallet.net_buy_usd * _wallet_weight(wallet), 2),
        )
        for wallet in eligible
    )
    weighted_buy_usd = sum(row.weighted_buy_usd for row in contributions)
    average_quality = (
        sum(wallet.quality for wallet in eligible) / len(eligible) if eligible else 0.0
    )

    breadth_component = min(
        len(eligible) / policy.target_distinct_wallets,
        1.0,
    ) * 30.0
    capital_component = min(
        weighted_buy_usd / policy.target_weighted_buy_usd,
        1.0,
    ) * 50.0
    quality_component = average_quality * 20.0
    score = round(breadth_component + capital_component + quality_component, 2)

    gates = (
        _gate(
            "liquidity",
            snapshot.liquidity_usd >= policy.min_liquidity_usd,
            f"${snapshot.liquidity_usd:,.0f}",
            f">= ${policy.min_liquidity_usd:,.0f}",
        ),
        _gate(
            "volume_24h",
            snapshot.volume_24h_usd >= policy.min_volume_24h_usd,
            f"${snapshot.volume_24h_usd:,.0f}",
            f">= ${policy.min_volume_24h_usd:,.0f}",
        ),
        _gate(
            "holder_concentration",
            snapshot.top_10_holder_ratio <= policy.max_top_10_holder_ratio,
            f"{snapshot.top_10_holder_ratio:.1%}",
            f"<= {policy.max_top_10_holder_ratio:.1%}",
        ),
        _gate(
            "mint_authority",
            not snapshot.mint_authority_enabled,
            "enabled" if snapshot.mint_authority_enabled else "disabled",
            "disabled",
        ),
        _gate(
            "freeze_authority",
            not snapshot.freeze_authority_enabled,
            "enabled" if snapshot.freeze_authority_enabled else "disabled",
            "disabled",
        ),
        _gate(
            "wallet_breadth",
            len(eligible) >= policy.min_distinct_wallets,
            str(len(eligible)),
            f">= {policy.min_distinct_wallets}",
        ),
        _gate(
            "accumulation_score",
            score >= policy.min_accumulation_score,
            f"{score:.2f}",
            f">= {policy.min_accumulation_score:.2f}",
        ),
    )

    failed_gates = tuple(gate for gate in gates if not gate.passed)
    decision = "WATCH" if not failed_gates else "REJECT"
    if failed_gates:
        explanation = tuple(
            f"{gate.name} failed: observed {gate.observed}; required {gate.requirement}"
            for gate in failed_gates
        )
    else:
        explanation = (
            "All public demo gates passed.",
            "WATCH means research priority only; it is not a trade instruction.",
        )

    return Evaluation(
        symbol=snapshot.symbol,
        decision=decision,
        accumulation_score=score,
        eligible_wallet_count=len(eligible),
        excluded_wallet_count=len(snapshot.wallets) - len(eligible),
        weighted_buy_usd=round(weighted_buy_usd, 2),
        contributions=contributions,
        gates=gates,
        explanation=explanation,
    )



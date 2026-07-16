"""Input models and validation for the public demo.

The models deliberately contain only the small set of fields needed to explain
the example. They are not a copy of the production scanner's data model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any, Mapping, Sequence


def _finite(value: float, field_name: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _non_negative(value: float, field_name: str) -> float:
    number = _finite(value, field_name)
    if number < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return number


def _ratio(value: float, field_name: str) -> float:
    number = _finite(value, field_name)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return number


@dataclass(frozen=True, slots=True)
class WalletObservation:
    """A synthetic wallet's net activity over the observation window."""

    wallet_id: str
    net_buy_usd: float
    quality: float

    def __post_init__(self) -> None:
        if not self.wallet_id.strip():
            raise ValueError("wallet_id must not be empty")
        object.__setattr__(self, "net_buy_usd", _finite(self.net_buy_usd, "net_buy_usd"))
        object.__setattr__(self, "quality", _ratio(self.quality, "quality"))

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "WalletObservation":
        return cls(
            wallet_id=str(raw["wallet_id"]),
            net_buy_usd=float(raw["net_buy_usd"]),
            quality=float(raw["quality"]),
        )


@dataclass(frozen=True, slots=True)
class TokenSnapshot:
    """Market and wallet observations for one synthetic token snapshot."""

    symbol: str
    liquidity_usd: float
    volume_24h_usd: float
    top_10_holder_ratio: float
    mint_authority_enabled: bool
    freeze_authority_enabled: bool
    wallets: tuple[WalletObservation, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        object.__setattr__(
            self, "liquidity_usd", _non_negative(self.liquidity_usd, "liquidity_usd")
        )
        object.__setattr__(
            self, "volume_24h_usd", _non_negative(self.volume_24h_usd, "volume_24h_usd")
        )
        object.__setattr__(
            self,
            "top_10_holder_ratio",
            _ratio(self.top_10_holder_ratio, "top_10_holder_ratio"),
        )
        object.__setattr__(self, "wallets", tuple(self.wallets))

        wallet_ids = [wallet.wallet_id for wallet in self.wallets]
        if len(wallet_ids) != len(set(wallet_ids)):
            raise ValueError("wallet_id values must be unique within a snapshot")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "TokenSnapshot":
        wallet_rows: Sequence[Mapping[str, Any]] = raw.get("wallets", ())
        mint_authority = raw["mint_authority_enabled"]
        freeze_authority = raw["freeze_authority_enabled"]
        if not isinstance(mint_authority, bool):
            raise ValueError("mint_authority_enabled must be a JSON boolean")
        if not isinstance(freeze_authority, bool):
            raise ValueError("freeze_authority_enabled must be a JSON boolean")
        return cls(
            symbol=str(raw["symbol"]),
            liquidity_usd=float(raw["liquidity_usd"]),
            volume_24h_usd=float(raw["volume_24h_usd"]),
            top_10_holder_ratio=float(raw["top_10_holder_ratio"]),
            mint_authority_enabled=mint_authority,
            freeze_authority_enabled=freeze_authority,
            wallets=tuple(WalletObservation.from_mapping(row) for row in wallet_rows),
        )


@dataclass(frozen=True, slots=True)
class EvaluationPolicy:
    """Readable demo thresholds; these are not production calibration values."""

    dust_threshold_usd: float = 500.0
    min_liquidity_usd: float = 50_000.0
    min_volume_24h_usd: float = 100_000.0
    max_top_10_holder_ratio: float = 0.65
    min_distinct_wallets: int = 3
    target_distinct_wallets: int = 5
    target_weighted_buy_usd: float = 20_000.0
    min_accumulation_score: float = 60.0

    def __post_init__(self) -> None:
        for field_name in (
            "dust_threshold_usd",
            "min_liquidity_usd",
            "min_volume_24h_usd",
            "target_weighted_buy_usd",
            "min_accumulation_score",
        ):
            _non_negative(getattr(self, field_name), field_name)
        _ratio(self.max_top_10_holder_ratio, "max_top_10_holder_ratio")
        if self.min_distinct_wallets < 1:
            raise ValueError("min_distinct_wallets must be at least 1")
        if self.target_distinct_wallets < self.min_distinct_wallets:
            raise ValueError("target_distinct_wallets must be >= min_distinct_wallets")
        if self.target_weighted_buy_usd == 0:
            raise ValueError("target_weighted_buy_usd must be greater than 0")
        if self.min_accumulation_score > 100:
            raise ValueError("min_accumulation_score must be <= 100")


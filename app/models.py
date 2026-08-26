from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True, slots=True)
class Faucet:
    faucet_id: str
    name: str
    url: str
    description: str = ""

    paid_7d_usd: Decimal = Decimal("0")
    users_paid: int = 0
    rating: Optional[Decimal] = None
    health: Optional[int] = None

    coins: tuple[str, ...] = field(default_factory=tuple)

    discovered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.faucet_id.strip():
            raise ValueError("faucet_id cannot be empty")

        if not self.name.strip():
            raise ValueError("faucet name cannot be empty")

        if not self.url.strip():
            raise ValueError("faucet URL cannot be empty")

        if self.paid_7d_usd < 0:
            raise ValueError("paid_7d_usd cannot be negative")

        if self.users_paid < 0:
            raise ValueError("users_paid cannot be negative")

        if self.health is not None and not 0 <= self.health <= 100:
            raise ValueError("health must be between 0 and 100")

        if self.rating is not None and self.rating < 0:
            raise ValueError("rating cannot be negative")


@dataclass(frozen=True, slots=True)
class Task:
    task_id: str
    faucet_id: str
    name: str
    task_type: str

    reward: Decimal
    estimated_seconds: int
    cooldown_seconds: int

    success_rate: float = 0.0
    currency: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id cannot be empty")

        if not self.faucet_id.strip():
            raise ValueError("faucet_id cannot be empty")

        if not self.name.strip():
            raise ValueError("task name cannot be empty")

        if not self.task_type.strip():
            raise ValueError("task_type cannot be empty")

        if self.reward < 0:
            raise ValueError("reward cannot be negative")

        if self.estimated_seconds < 0:
            raise ValueError(
                "estimated_seconds cannot be negative"
            )

        if self.cooldown_seconds < 0:
            raise ValueError(
                "cooldown_seconds cannot be negative"
            )

        if not 0.0 <= self.success_rate <= 1.0:
            raise ValueError(
                "success_rate must be between 0.0 and 1.0"
            )


@dataclass(frozen=True, slots=True)
class TaskScore:
    task: Task

    profitability: Decimal
    cooldown_factor: Decimal
    success_factor: Decimal

    score: Decimal


@dataclass(frozen=True, slots=True)
class BalanceSnapshot:
    currency: str
    balance: Decimal

    captured_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.currency.strip():
            raise ValueError("currency cannot be empty")

        if self.balance < 0:
            raise ValueError("balance cannot be negative")


@dataclass(frozen=True, slots=True)
class EarningRecord:
    faucet_id: str
    task_id: str
    task_type: str

    currency: str

    expected_amount: Decimal
    actual_amount: Decimal

    duration_seconds: float
    success: bool

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    error: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.faucet_id.strip():
            raise ValueError("faucet_id cannot be empty")

        if not self.task_id.strip():
            raise ValueError("task_id cannot be empty")

        if not self.task_type.strip():
            raise ValueError("task_type cannot be empty")

        if not self.currency.strip():
            raise ValueError("currency cannot be empty")

        if self.expected_amount < 0:
            raise ValueError(
                "expected_amount cannot be negative"
            )

        if self.actual_amount < 0:
            raise ValueError(
                "actual_amount cannot be negative"
            )

        if self.duration_seconds < 0:
            raise ValueError(
                "duration_seconds cannot be negative"
            )


@dataclass(frozen=True, slots=True)
class TaskExecutionResult:
    task_id: str

    started_at: datetime
    finished_at: datetime

    success: bool

    expected_reward: Decimal
    actual_reward: Decimal

    currency: str

    error: Optional[str] = None

    @property
    def duration_seconds(self) -> float:
        return (
            self.finished_at - self.started_at
        ).total_seconds()

    @property
    def reward_delta(self) -> Decimal:
        return self.actual_reward - self.expected_reward


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    faucets: tuple[Faucet, ...]

    discovered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def count(self) -> int:
        return len(self.faucets)

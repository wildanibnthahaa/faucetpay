from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    path: str


@dataclass(frozen=True, slots=True)
class BrowserConfig:
    enabled: bool
    headless: bool
    timeout_ms: int


@dataclass(frozen=True, slots=True)
class DiscoveryConfig:
    enabled: bool
    directory_url: str
    refresh_seconds: int
    max_faucets: int


@dataclass(frozen=True, slots=True)
class ScoringConfig:
    cooldown_weight: float
    success_weight: float
    minimum_score: float


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    enabled: bool
    interval_seconds: int
    max_tasks_per_cycle: int


@dataclass(frozen=True, slots=True)
class AppConfig:
    database: DatabaseConfig
    browser: BrowserConfig
    discovery: DiscoveryConfig
    scoring: ScoringConfig
    scheduler: SchedulerConfig


def _section(
    raw: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    value = raw.get(name, {})

    if value is None:
        return {}

    if not isinstance(value, dict):
        raise ValueError(
            f"Configuration section '{name}' must be a mapping."
        )

    return value


def _positive_int(
    value: Any,
    name: str,
) -> int:
    result = int(value)

    if result <= 0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return result


def _non_negative_float(
    value: Any,
    name: str,
) -> float:
    result = float(value)

    if result < 0:
        raise ValueError(
            f"{name} cannot be negative."
        )

    return result


def load_config(
    path: str | Path,
) -> AppConfig:
    """
    Load and validate application configuration from YAML.
    """

    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    if not config_path.is_file():
        raise ValueError(
            f"Configuration path is not a file: {config_path}"
        )

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        raw = yaml.safe_load(handle)

    if raw is None:
        raw = {}

    if not isinstance(raw, dict):
        raise ValueError(
            "Root configuration must be a YAML mapping."
        )

    database = _section(raw, "database")
    browser = _section(raw, "browser")
    discovery = _section(raw, "discovery")
    scoring = _section(raw, "scoring")
    scheduler = _section(raw, "scheduler")

    database_path = str(
        database.get(
            "path",
            "./data/recovery.db",
        )
    ).strip()

    if not database_path:
        raise ValueError(
            "database.path cannot be empty."
        )

    directory_url = str(
        discovery.get(
            "directory_url",
            "https://faucetpay.io/faucets",
        )
    ).strip()

    if not directory_url:
        raise ValueError(
            "discovery.directory_url cannot be empty."
        )

    cooldown_weight = _non_negative_float(
        scoring.get(
            "cooldown_weight",
            0.15,
        ),
        "scoring.cooldown_weight",
    )

    success_weight = _non_negative_float(
        scoring.get(
            "success_weight",
            0.25,
        ),
        "scoring.success_weight",
    )

    minimum_score = _non_negative_float(
        scoring.get(
            "minimum_score",
            0.0,
        ),
        "scoring.minimum_score",
    )

    if cooldown_weight > 1:
        raise ValueError(
            "scoring.cooldown_weight must be <= 1."
        )

    if success_weight > 1:
        raise ValueError(
            "scoring.success_weight must be <= 1."
        )

    return AppConfig(
        database=DatabaseConfig(
            path=database_path,
        ),
        browser=BrowserConfig(
            enabled=bool(
                browser.get(
                    "enabled",
                    True,
                )
            ),
            headless=bool(
                browser.get(
                    "headless",
                    True,
                )
            ),
            timeout_ms=_positive_int(
                browser.get(
                    "timeout_ms",
                    30000,
                ),
                "browser.timeout_ms",
            ),
        ),
        discovery=DiscoveryConfig(
            enabled=bool(
                discovery.get(
                    "enabled",
                    True,
                )
            ),
            directory_url=directory_url,
            refresh_seconds=_positive_int(
                discovery.get(
                    "refresh_seconds",
                    3600,
                ),
                "discovery.refresh_seconds",
            ),
            max_faucets=_positive_int(
                discovery.get(
                    "max_faucets",
                    250,
                ),
                "discovery.max_faucets",
            ),
        ),
        scoring=ScoringConfig(
            cooldown_weight=cooldown_weight,
            success_weight=success_weight,
            minimum_score=minimum_score,
        ),
        scheduler=SchedulerConfig(
            enabled=bool(
                scheduler.get(
                    "enabled",
                    True,
                )
            ),
            interval_seconds=_positive_int(
                scheduler.get(
                    "interval_seconds",
                    3600,
                ),
                "scheduler.interval_seconds",
            ),
            max_tasks_per_cycle=_positive_int(
                scheduler.get(
                    "max_tasks_per_cycle",
                    50,
                ),
                "scheduler.max_tasks_per_cycle",
            ),
        ),
    )

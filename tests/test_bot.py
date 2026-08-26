from decimal import Decimal

import pytest

from app.bot import Bot
from app.config import (
    AppConfig,
    BrowserConfig,
    DatabaseConfig,
    DiscoveryConfig,
    SchedulerConfig,
    ScoringConfig,
)
from app.database import Database
from app.models import Faucet, Task


@pytest.fixture
def config(tmp_path):
    return AppConfig(
        database=DatabaseConfig(
            path=str(
                tmp_path / "recovery.db"
            )
        ),
        browser=BrowserConfig(
            enabled=False,
            headless=True,
            timeout_ms=5000,
        ),
        discovery=DiscoveryConfig(
            enabled=False,
            directory_url=(
                "https://faucetpay.io/faucets"
            ),
            refresh_seconds=3600,
            max_pages=1,
        ),
        scoring=ScoringConfig(
            cooldown_weight=0.15,
            success_weight=0.25,
            minimum_score=0,
        ),
        scheduler=SchedulerConfig(
            enabled=True,
            interval_seconds=3600,
            max_tasks_per_cycle=10,
        ),
    )


@pytest.mark.asyncio
async def test_bot_ranks_provider_tasks(
    config,
):
    database = Database(
        config.database.path
    )

    database.initialize()

    faucet = Faucet(
        faucet_id="1",
        name="Test Faucet",
        url="https://example.com",
    )

    async def provider(faucets):
        assert faucets == [faucet]

        return [
            Task(
                task_id="fast",
                faucet_id="1",
                name="Fast",
                task_type="claim",
                reward=Decimal("10"),
                estimated_seconds=10,
                cooldown_seconds=10,
                success_rate=1,
            ),
            Task(
                task_id="slow",
                faucet_id="1",
                name="Slow",
                task_type="claim",
                reward=Decimal("1"),
                estimated_seconds=100,
                cooldown_seconds=10,
                success_rate=1,
            ),
        ]

    bot = Bot(
        config,
        database,
        task_provider=provider,
    )

    ranked = await bot.build_ranked_queue(
        [faucet]
    )

    assert ranked

    assert (
        ranked[0].task.task_id
        == "fast"
    )

    await bot.discovery.close()

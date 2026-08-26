from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from typing import Awaitable, Callable

from .config import AppConfig, load_config
from .database import Database
from .discovery import FaucetPayDirectory
from .models import Faucet, Task, TaskScore
from .scoring import TaskScorer


logger = logging.getLogger(__name__)


TaskProvider = Callable[
    [list[Faucet]],
    Awaitable[list[Task]],
]


class Bot:
    """
    Core scheduler untuk FaucetPay recovery/monitoring.

    Flow:

        discovery
            ↓
        database
            ↓
        task provider
            ↓
        scoring
            ↓
        ranked queue

    Tidak melakukan:
    - CAPTCHA solving
    - proxy rotation
    - fingerprint bypass
    - claim otomatis
    - PTC automation
    - offerwall completion
    - withdrawal
    """

    def __init__(
        self,
        config: AppConfig,
        database: Database,
        task_provider: TaskProvider | None = None,
    ) -> None:
        self.config = config
        self.database = database

        self.discovery = FaucetPayDirectory(
            directory_url=(
                config.discovery.directory_url
            ),
            timeout_ms=(
                config.browser.timeout_ms
            ),
            headless=(
                config.browser.headless
            ),
        )

        self.scorer = TaskScorer(
            cooldown_weight=(
                config.scoring.cooldown_weight
            ),
            success_weight=(
                config.scoring.success_weight
            ),
        )

        self.task_provider = (
            task_provider
            or self._default_task_provider
        )

        self._stop_event = asyncio.Event()
        self._running = False

    async def _default_task_provider(
        self,
        faucets: list[Faucet],
    ) -> list[Task]:
        """
        Default provider.

        Saat ini kosong karena public FaucetPay
        directory tidak digunakan untuk mengarang
        data task earning.

        Nantinya provider yang sah dapat dipasang
        melalui dependency injection.
        """
        return []

    async def discover(self) -> list[Faucet]:
        """
        Jalankan discovery dan simpan faucet
        ke SQLite.
        """
        if not self.config.discovery.enabled:
            logger.info(
                "Discovery disabled by configuration."
            )
            return []

        logger.info(
            "Starting FaucetPay directory discovery..."
        )

        faucets = await self.discovery.discover(
            max_faucets=(
                self.config.discovery.max_pages
            ),
        )

        for faucet in faucets:
            self.database.upsert_faucet(
                faucet
            )

        logger.info(
            "Discovery complete: %d faucets.",
            len(faucets),
        )

        return faucets

    async def build_ranked_queue(
        self,
        faucets: list[Faucet],
    ) -> list[TaskScore]:
        """
        Ambil task dari provider lalu ranking.
        """
        tasks = await self.task_provider(
            faucets
        )

        logger.info(
            "Task provider returned %d tasks.",
            len(tasks),
        )

        for task in tasks:
            self.database.upsert_task(task)

        ranked = self.scorer.rank(tasks)

        minimum_score = DecimalCompat(
            self.config.scoring.minimum_score
        )

        ranked = [
            item
            for item in ranked
            if item.score >= minimum_score
        ]

        max_tasks = (
            self.config
            .scheduler
            .max_tasks_per_cycle
        )

        return ranked[:max_tasks]

    async def run_cycle(self) -> list[TaskScore]:
        """
        Jalankan satu siklus penuh.
        """
        logger.info(
            "Starting scheduler cycle."
        )

        faucets = await self.discover()

        ranked = await self.build_ranked_queue(
            faucets
        )

        logger.info(
            "Cycle complete: %d ranked tasks.",
            len(ranked),
        )

        for position, result in enumerate(
            ranked,
            start=1,
        ):
            logger.info(
                "#%d task=%s score=%s "
                "profitability=%s reward=%s",
                position,
                result.task.name,
                result.score,
                result.profitability,
                result.task.reward,
            )

        return ranked

    async def run(self) -> None:
        """
        Jalankan scheduler secara terus-menerus.
        """
        if self._running:
            raise RuntimeError(
                "Bot is already running."
            )

        self._running = True

        logger.info(
            "Bot scheduler started."
        )

        try:
            while not self._stop_event.is_set():
                try:
                    await self.run_cycle()

                except asyncio.CancelledError:
                    raise

                except Exception:
                    logger.exception(
                        "Scheduler cycle failed."
                    )

                interval = (
                    self.config
                    .scheduler
                    .interval_seconds
                )

                logger.info(
                    "Next cycle in %d seconds.",
                    interval,
                )

                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=interval,
                    )

                except asyncio.TimeoutError:
                    continue

        finally:
            self._running = False

            await self.discovery.close()

            logger.info(
                "Bot scheduler stopped."
            )

    def stop(self) -> None:
        """
        Minta scheduler berhenti setelah cycle
        berjalan selesai.
        """
        if not self._stop_event.is_set():
            logger.info(
                "Stop requested."
            )

            self._stop_event.set()


def DecimalCompat(value: float):
    """
    Helper kecil untuk menghindari import Decimal
    di banyak tempat pada orchestrator.

    Menghasilkan Decimal dari string agar tidak
    terkena floating-point representation.
    """
    from decimal import Decimal

    return Decimal(str(value))


async def run_application(
    config_path: str,
    once: bool = False,
) -> None:
    """
    Application entrypoint yang dapat dipakai
    oleh CLI maupun module runner.
    """
    config = load_config(config_path)

    database = Database(
        config.database.path
    )

    database.initialize()

    bot = Bot(
        config=config,
        database=database,
    )

    if once:
        try:
            await bot.run_cycle()
        finally:
            await bot.discovery.close()

        return

    loop = asyncio.get_running_loop()

    for sig in (
        signal.SIGINT,
        signal.SIGTERM,
    ):
        try:
            loop.add_signal_handler(
                sig,
                bot.stop,
            )
        except NotImplementedError:
            # Signal handlers tidak tersedia
            # pada sebagian environment/platform.
            pass

    await bot.run()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "FaucetPay read-only recovery "
            "scheduler"
        )
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML configuration.",
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "Run one discovery/scoring cycle "
            "and exit."
        ),
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    await run_application(
        config_path=args.config,
        once=args.once,
    )


if __name__ == "__main__":
    asyncio.run(main())

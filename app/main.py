from __future__ import annotations

import asyncio
import logging

from .bot import run_application


logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main entry point aplikasi.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="FaucetPay Recovery Core"
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path ke file konfigurasi YAML.",
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "Jalankan satu cycle discovery/scoring "
            "kemudian keluar."
        ),
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            run_application(
                config_path=args.config,
                once=args.once,
            )
        )

    except KeyboardInterrupt:
        logger.info(
            "Application interrupted by user."
        )


if __name__ == "__main__":
    main()

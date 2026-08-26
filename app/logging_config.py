from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


DEFAULT_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


def setup_logging(
    log_file: str = "./logs/faucetpay.log",
    level: str = "INFO",
    max_bytes: int = 5_000_000,
    backup_count: int = 5,
) -> None:
    """
    Configure application logging.

    Output:
    - stdout/console
    - rotating log file

    max_bytes:
        Ukuran maksimum satu file log.

    backup_count:
        Jumlah file backup yang disimpan.
    """

    log_path = Path(log_file)
    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    numeric_level = getattr(
        logging,
        level.upper(),
        logging.INFO,
    )

    formatter = logging.Formatter(
        DEFAULT_FORMAT
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        formatter
    )

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    file_handler.setFormatter(
        formatter
    )

    root_logger = logging.getLogger()

    root_logger.setLevel(
        numeric_level
    )

    # Hindari duplicate handler jika fungsi
    # dipanggil lebih dari satu kali.
    root_logger.handlers.clear()

    root_logger.addHandler(
        console_handler
    )

    root_logger.addHandler(
        file_handler
    )


def get_logger(
    name: str,
) -> logging.Logger:
    """
    Ambil logger berdasarkan nama module.
    """
    return logging.getLogger(name)

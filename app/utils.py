from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def parse_money(value: str | int | float | Decimal) -> Decimal:
    """
    Parse nilai uang menjadi Decimal.

    Contoh:
        "$1,234.50" -> Decimal("1234.50")
        "1234.50"   -> Decimal("1234.50")
        ""           -> Decimal("0")
    """
    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(str(value))

    cleaned = (
        str(value)
        .replace("$", "")
        .replace(",", "")
        .strip()
    )

    if not cleaned:
        return Decimal("0")

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def parse_integer(
    value: str | int | float | None,
) -> int:
    """
    Ambil integer dari sebuah nilai.

    Contoh:
        "1,234 users" -> 1234
        "500"         -> 500
        ""            -> 0
    """
    if value is None:
        return 0

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    match = re.search(
        r"-?\d[\d,]*",
        str(value),
    )

    if not match:
        return 0

    try:
        return int(
            match.group(0).replace(",", "")
        )
    except ValueError:
        return 0


def parse_rating(
    value: str | int | float | Decimal | None,
) -> Decimal | None:
    """
    Parse rating menjadi Decimal.

    Contoh:
        "Rating 4.7" -> Decimal("4.7")
        "4.5/5"      -> Decimal("4.5")
        None         -> None
    """
    if value is None:
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(str(value))

    match = re.search(
        r"\d+(?:\.\d+)?",
        str(value),
    )

    if not match:
        return None

    try:
        return Decimal(match.group(0))
    except InvalidOperation:
        return None


def clamp(
    value: float | Decimal,
    minimum: float | Decimal,
    maximum: float | Decimal,
) -> float | Decimal:
    """
    Batasi nilai antara minimum dan maximum.
    """
    if value < minimum:
        return minimum

    if value > maximum:
        return maximum

    return value


def normalize_text(
    value: str | None,
) -> str:
    """
    Bersihkan whitespace berlebihan.
    """
    if value is None:
        return ""

    return " ".join(
        str(value).split()
    )


def safe_int(
    value: object,
    default: int = 0,
) -> int:
    """
    Konversi aman ke integer.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_decimal(
    value: object,
    default: Decimal = Decimal("0"),
) -> Decimal:
    """
    Konversi aman ke Decimal.
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def percentage(
    part: Decimal | float | int,
    total: Decimal | float | int,
) -> Decimal:
    """
    Hitung persentase dengan aman.

    Jika total = 0, hasil = 0.
    """
    total_decimal = Decimal(str(total))

    if total_decimal == 0:
        return Decimal("0")

    return (
        Decimal(str(part))
        / total_decimal
        * Decimal("100")
    )

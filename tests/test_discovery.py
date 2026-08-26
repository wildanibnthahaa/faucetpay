from decimal import Decimal

from app.discovery import (
    FaucetPayDirectory,
    parse_integer,
    parse_money,
    parse_rating,
)


def test_parse_money():
    assert parse_money(
        "$1,234.50"
    ) == Decimal("1234.50")


def test_parse_money_invalid():
    assert parse_money(
        "not money"
    ) == Decimal("0")


def test_parse_integer():
    assert parse_integer(
        "1,234 users"
    ) == 1234


def test_parse_integer_missing():
    assert parse_integer(
        "no number"
    ) == 0


def test_parse_rating():
    assert parse_rating(
        "Rating 4.7"
    ) == Decimal("4.7")


def test_parse_rating_missing():
    assert parse_rating(
        "unknown"
    ) is None


def test_extract_faucet_links():
    from bs4 import BeautifulSoup

    html = """
    <html>
      <body>
        <a href="/faucets/id/123">
          Faucet One
        </a>
        <a href="/faucets/id/456">
          Faucet Two
        </a>
        <a href="/other">
          Ignore
        </a>
        <a href="/faucets/id/123">
          Duplicate
        </a>
      </body>
    </html>
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    links = (
        FaucetPayDirectory
        ._extract_faucet_links(
            soup,
            "https://faucetpay.io/faucets",
        )
    )

    assert len(links) == 2

    urls = {
        url for _, url in links
    }

    assert (
        "https://faucetpay.io/faucets/id/123"
        in urls
    )

    assert (
        "https://faucetpay.io/faucets/id/456"
        in urls
    )


def test_parse_detail():
    html = """
    <html>
      <body>
        <h1>Test Faucet</h1>
        <p>Paid this week $12.34</p>
        <p>Users paid 321</p>
        <p>Rating 4.6</p>
        <p>Health 88</p>
        <p>Coins paid BTC TRX USDT</p>
      </body>
    </html>
    """

    faucet = (
        FaucetPayDirectory._parse_detail(
            "Fallback",
            "https://faucetpay.io/faucets/id/123",
            html,
        )
    )

    assert faucet.faucet_id == "123"
    assert faucet.name == "Test Faucet"
    assert faucet.paid_7d_usd == Decimal("12.34")
    assert faucet.users_paid == 321
    assert faucet.rating == Decimal("4.6")
    assert faucet.health == 88
    assert "BTC" in faucet.coins
    assert "TRX" in faucet.coins

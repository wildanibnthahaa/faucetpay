from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from .models import Faucet


CURRENCY_MAP = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "tether": "USDT",
    "litecoin": "LTC",
    "dogecoin": "DOGE",
    "bitcoin-cash": "BCH",
    "dash": "DASH",
    "digibyte": "DGB",
    "tron": "TRX",
    "zcash": "ZEC",
    "solana": "SOL",
    "bnb": "BNB",
    "feyorra": "FEY",
    "usd-coin": "USDC",
}


def parse_money(value: str) -> Decimal:
    """Convert values such as '$1,234.50' into Decimal."""
    cleaned = (
        value.replace("$", "")
        .replace(",", "")
        .strip()
    )

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def parse_integer(value: str) -> int:
    """Extract an integer from text such as '1,234 users'."""
    match = re.search(r"[\d,]+", value)

    if not match:
        return 0

    try:
        return int(match.group(0).replace(",", ""))
    except ValueError:
        return 0


def parse_rating(value: str) -> Decimal | None:
    """Extract a decimal rating from text."""
    match = re.search(r"\d+(?:\.\d+)?", value)

    if not match:
        return None

    try:
        return Decimal(match.group(0))
    except InvalidOperation:
        return None


class FaucetPayDirectory:
    """
    Read-only FaucetPay public-directory collector.

    This module only reads public directory/detail pages.
    It does not:
    - log into accounts
    - submit claims
    - complete offers
    - solve CAPTCHAs
    - bypass anti-bot controls
    - perform withdrawals
    """

    def __init__(
        self,
        directory_url: str,
        timeout_ms: int = 30_000,
        headless: bool = True,
    ) -> None:
        self.directory_url = directory_url
        self.timeout_ms = timeout_ms
        self.headless = headless

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def start(self) -> None:
        """Start Playwright and Chromium."""
        if self._context is not None:
            return

        self._playwright = await async_playwright().start()

        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
        )

        self._context = await self._browser.new_context()

    async def close(self) -> None:
        """Close browser resources safely."""
        if self._context is not None:
            await self._context.close()

        if self._browser is not None:
            await self._browser.close()

        if self._playwright is not None:
            await self._playwright.stop()

        self._context = None
        self._browser = None
        self._playwright = None

    async def _new_page(self) -> Page:
        """Create a new browser page."""
        if self._context is None:
            await self.start()

        assert self._context is not None
        return await self._context.new_page()

    @staticmethod
    def extract_faucet_links(
        html: str | BeautifulSoup,
        base_url: str,
    ) -> list[tuple[str, str]]:
        """
        Extract faucet detail links from directory HTML.
        """
        soup = (
            html
            if isinstance(html, BeautifulSoup)
            else BeautifulSoup(html, "html.parser")
        )

        results: dict[str, tuple[str, str]] = {}

        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"])
            name = anchor.get_text(" ", strip=True)

            if "/faucets/id/" not in href:
                continue

            if not name:
                continue

            url = urljoin(base_url, href)

            results[url] = (name, url)

        return list(results.values())

    @staticmethod
    def _extract_faucet_links(
        html: str,
        base_url: str,
    ) -> list[tuple[str, str]]:
        return FaucetPayDirectory.extract_faucet_links(
            html,
            base_url,
        )

    @staticmethod
    def parse_detail(
        name_hint: str,
        url: str,
        html: str,
    ) -> Faucet:
        """Parse a public faucet detail page."""
        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("h1")

        name = (
            title.get_text(" ", strip=True)
            if title
            else name_hint
        )

        text = soup.get_text(" ", strip=True)

        paid_match = re.search(
            r"Paid\s+this\s+week\s+\$?([\d,.]+)",
            text,
            re.IGNORECASE,
        )

        users_match = re.search(
            r"Users\s+paid\s+([\d,]+)",
            text,
            re.IGNORECASE,
        )

        rating_match = re.search(
            r"Rating\s+([\d.]+)",
            text,
            re.IGNORECASE,
        )

        health_match = re.search(
            r"Health\s+(\d+)",
            text,
            re.IGNORECASE,
        )

        coins: list[str] = []

        for coin_name, symbol in CURRENCY_MAP.items():
            if re.search(
                rf"\b{re.escape(symbol)}\b",
                text,
                re.IGNORECASE,
            ):
                coins.append(symbol)

        faucet_id_match = re.search(
            r"/faucets/id/([^/?#]+)",
            url,
            re.IGNORECASE,
        )

        faucet_id = (
            faucet_id_match.group(1)
            if faucet_id_match
            else url
        )

        return Faucet(
            faucet_id=faucet_id,
            name=name,
            url=url,
            description=text[:1000],
            paid_7d_usd=(
                parse_money(paid_match.group(1))
                if paid_match
                else Decimal("0")
            ),
            users_paid=(
                parse_integer(users_match.group(1))
                if users_match
                else 0
            ),
            rating=(
                parse_rating(rating_match.group(1))
                if rating_match
                else None
            ),
            health=(
                parse_integer(health_match.group(1))
                if health_match
                else None
            ),
            coins=tuple(sorted(set(coins))),
            discovered_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _parse_detail(
        name_hint: str,
        url: str,
        html: str,
    ) -> Faucet:
        return FaucetPayDirectory.parse_detail(
            name_hint,
            url,
            html,
        )

    async def discover(
        self,
        max_faucets: int = 250,
    ) -> list[Faucet]:
        """
        Discover public faucets from FaucetPay.

        Only GET/read operations are performed.
        """
        page = await self._new_page()

        try:
            await page.goto(
                self.directory_url,
                wait_until="domcontentloaded",
                timeout=self.timeout_ms,
            )

            html = await page.content()

            links = self.extract_faucet_links(
                html,
                self.directory_url,
            )

        finally:
            await page.close()

        faucets: list[Faucet] = []

        assert self._context is not None

        for name, url in links[:max_faucets]:
            detail_page = await self._context.new_page()

            try:
                await detail_page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )

                detail_html = await detail_page.content()

                faucet = self.parse_detail(
                    name,
                    url,
                    detail_html,
                )

                faucets.append(faucet)

            except Exception:
                # One broken faucet page should not stop discovery.
                continue

            finally:
                await detail_page.close()

        return faucets


async def discover_once(
    directory_url: str,
    max_faucets: int = 250,
    timeout_ms: int = 30_000,
) -> list[Faucet]:
    """Convenience function for a single discovery run."""
    collector = FaucetPayDirectory(
        directory_url=directory_url,
        timeout_ms=timeout_ms,
    )

    try:
        return await collector.discover(
            max_faucets=max_faucets,
        )
    finally:
        await collector.close()

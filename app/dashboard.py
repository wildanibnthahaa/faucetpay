from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from .config import load_config
from .database import Database


def render(config_path: str) -> None:
    """
    Tampilkan dashboard dari database SQLite.
    """
    config = load_config(config_path)

    database = Database(
        config.database.path
    )

    database.initialize()

    console = Console()

    console.print()
    console.print(
        "[bold]FaucetPay Recovery Dashboard[/bold]"
    )
    console.print()

    # --------------------------------------------------
    # Faucet summary
    # --------------------------------------------------

    faucets = database.list_faucets()

    faucet_table = Table(
        title=f"Faucets ({len(faucets)})"
    )

    faucet_table.add_column("ID")
    faucet_table.add_column("Name")
    faucet_table.add_column(
        "Paid 7d USD",
        justify="right",
    )
    faucet_table.add_column(
        "Users",
        justify="right",
    )
    faucet_table.add_column(
        "Rating",
        justify="right",
    )
    faucet_table.add_column(
        "Health",
        justify="right",
    )

    for faucet in faucets:
        faucet_table.add_row(
            str(faucet["faucet_id"]),
            str(faucet["name"]),
            str(faucet["paid_7d_usd"]),
            str(faucet["users_paid"]),
            (
                str(faucet["rating"])
                if faucet["rating"] is not None
                else "-"
            ),
            (
                str(faucet["health"])
                if faucet["health"] is not None
                else "-"
            ),
        )

    console.print(faucet_table)
    console.print()

    # --------------------------------------------------
    # Task summary
    # --------------------------------------------------

    tasks = database.list_tasks(
        enabled_only=False
    )

    task_table = Table(
        title=f"Tasks ({len(tasks)})"
    )

    task_table.add_column("ID")
    task_table.add_column("Task")
    task_table.add_column("Type")
    task_table.add_column(
        "Reward",
        justify="right",
    )
    task_table.add_column(
        "Time",
        justify="right",
    )
    task_table.add_column(
        "Cooldown",
        justify="right",
    )
    task_table.add_column(
        "Success",
        justify="right",
    )
    task_table.add_column("Status")

    for task in tasks:
        status = (
            "[green]ENABLED[/green]"
            if task["enabled"]
            else "[red]DISABLED[/red]"
        )

        task_table.add_row(
            str(task["task_id"]),
            str(task["name"]),
            str(task["task_type"]),
            str(task["reward"]),
            f"{task['estimated_seconds']}s",
            f"{task['cooldown_seconds']}s",
            f"{task['success_rate']:.2%}",
            status,
        )

    console.print(task_table)
    console.print()

    # --------------------------------------------------
    # Earnings totals
    # --------------------------------------------------

    totals = database.totals()

    total_table = Table(
        title="Verified Earnings"
    )

    total_table.add_column("Currency")
    total_table.add_column(
        "Total",
        justify="right",
    )

    if totals:
        for currency, amount in totals.items():
            total_table.add_row(
                currency,
                format(amount, "f"),
            )
    else:
        total_table.add_row(
            "-",
            "0",
        )

    console.print(total_table)
    console.print()

    # --------------------------------------------------
    # Faucet statistics
    # --------------------------------------------------

    statistics = database.faucet_statistics()

    statistics_table = Table(
        title="Faucet Statistics"
    )

    statistics_table.add_column("Faucet")
    statistics_table.add_column(
        "Attempts",
        justify="right",
    )
    statistics_table.add_column(
        "Successes",
        justify="right",
    )
    statistics_table.add_column(
        "Earnings",
        justify="right",
    )

    for row in statistics:
        statistics_table.add_row(
            str(row["name"]),
            str(row["attempts"]),
            str(row["successes"] or 0),
            f"{float(row['earnings'] or 0):.12f}",
        )

    console.print(
        statistics_table
    )
    console.print()

    # --------------------------------------------------
    # Recent earnings
    # --------------------------------------------------

    recent = database.recent_earnings(
        limit=20
    )

    recent_table = Table(
        title="Recent Earnings"
    )

    recent_table.add_column("Time")
    recent_table.add_column("Task")
    recent_table.add_column("Type")
    recent_table.add_column("Currency")
    recent_table.add_column(
        "Expected",
        justify="right",
    )
    recent_table.add_column(
        "Actual",
        justify="right",
    )
    recent_table.add_column("Status")

    for row in recent:
        status = (
            "[green]PASS[/green]"
            if row["success"]
            else "[red]FAIL[/red]"
        )

        recent_table.add_row(
            str(row["created_at"]),
            str(row["task_id"]),
            str(row["task_type"]),
            str(row["currency"]),
            str(row["expected_amount"]),
            str(row["actual_amount"]),
            status,
        )

    console.print(
        recent_table
    )
    console.print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "FaucetPay Recovery CLI Dashboard"
        )
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config.yaml",
    )

    args = parser.parse_args()

    render(
        args.config
    )


if __name__ == "__main__":
    main()

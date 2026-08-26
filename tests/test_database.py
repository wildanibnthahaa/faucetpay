from datetime import datetime, timezone
from decimal import Decimal

from app.database import Database
from app.models import EarningRecord, Faucet, Task


def make_faucet():
    return Faucet(
        faucet_id="123",
        name="Test Faucet",
        url="https://example.com",
        paid_7d_usd=Decimal("12.50"),
        users_paid=100,
        rating=Decimal("4.5"),
        health=80,
        coins=("BTC", "TRX"),
        discovered_at=datetime.now(timezone.utc),
    )


def test_database_initializes(tmp_path):
    database = Database(
        str(tmp_path / "recovery.db")
    )

    database.initialize()

    assert (
        tmp_path / "recovery.db"
    ).exists()


def test_faucet_upsert(tmp_path):
    database = Database(
        str(tmp_path / "recovery.db")
    )

    database.initialize()

    database.upsert_faucet(
        make_faucet()
    )

    row = database.get_faucet("123")

    assert row is not None
    assert row["name"] == "Test Faucet"
    assert row["users_paid"] == 100


def test_faucet_upsert_updates_existing(tmp_path):
    database = Database(
        str(tmp_path / "recovery.db")
    )

    database.initialize()

    database.upsert_faucet(
        make_faucet()
    )

    updated = make_faucet()

    database.upsert_faucet(
        Faucet(
            faucet_id=updated.faucet_id,
            name="Updated Faucet",
            url=updated.url,
            paid_7d_usd=Decimal("99.00"),
            users_paid=500,
        )
    )

    row = database.get_faucet("123")

    assert row is not None
    assert row["name"] == "Updated Faucet"
    assert row["users_paid"] == 500


def test_task_upsert_and_list(tmp_path):
    database = Database(
        str(tmp_path / "recovery.db")
    )

    database.initialize()

    database.upsert_faucet(
        make_faucet()
    )

    task = Task(
        task_id="task-1",
        faucet_id="123",
        name="Test Claim",
        task_type="claim",
        reward=Decimal("100"),
        estimated_seconds=10,
        cooldown_seconds=60,
        success_rate=0.9,
    )

    database.upsert_task(task)

    tasks = database.list_tasks()

    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "task-1"
    assert tasks[0]["enabled"] == 1


def test_disable_task(tmp_path):
    database = Database(
        str(tmp_path / "recovery.db")
    )

    database.initialize()

    database.upsert_faucet(
        make_faucet()
    )

    database.upsert_task(
        Task(
            task_id="task-1",
            faucet_id="123",
            name="Test",
            task_type="claim",
            reward=Decimal("100"),
            estimated_seconds=10,
            cooldown_seconds=60,
        )
    )

    database.disable_task("task-1")

    assert database.list_tasks() == []
    assert len(
        database.list_tasks(
            enabled_only=False
        )
    ) == 1


def test_earning_record(tmp_path):
    database = Database(
        str(tmp_path / "recovery.db")
    )

    database.initialize()

    database.upsert_faucet(
        make_faucet()
    )

    record = EarningRecord(
        faucet_id="123",
        task_id="task-1",
        task_type="claim",
        currency="BTC",
        expected_amount=Decimal("100"),
        actual_amount=Decimal("100"),
        duration_seconds=3.2,
        success=True,
        created_at=datetime.now(
            timezone.utc
        ),
    )

    row_id = database.record_earning(
        record
    )

    assert row_id > 0

    totals = database.totals()

    assert totals["BTC"] == Decimal("100")


def test_failed_earning_not_in_totals(tmp_path):
    database = Database(
        str(tmp_path / "recovery.db")
    )

    database.initialize()

    database.upsert_faucet(
        make_faucet()
    )

    record = EarningRecord(
        faucet_id="123",
        task_id="task-1",
        task_type="claim",
        currency="BTC",
        expected_amount=Decimal("100"),
        actual_amount=Decimal("100"),
        duration_seconds=3,
        success=False,
        created_at=datetime.now(
            timezone.utc
        ),
        error="Test failure",
    )

    database.record_earning(record)

    assert "BTC" not in database.totals()

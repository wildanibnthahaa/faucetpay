from decimal import Decimal

from app.models import Task
from app.scoring import TaskScorer


def make_task(
    reward="100",
    estimated_seconds=10,
    cooldown_seconds=60,
    success_rate=1.0,
):
    return Task(
        task_id="task-1",
        faucet_id="faucet-1",
        name="Test Task",
        task_type="claim",
        reward=Decimal(reward),
        estimated_seconds=estimated_seconds,
        cooldown_seconds=cooldown_seconds,
        success_rate=success_rate,
    )


def test_profitable_task_scores_positive():
    scorer = TaskScorer()

    result = scorer.score(
        make_task()
    )

    assert result.score > 0
    assert (
        result.profitability
        == Decimal("10")
    )


def test_zero_duration_scores_zero():
    scorer = TaskScorer()

    result = scorer.score(
        make_task(
            estimated_seconds=0
        )
    )

    assert result.score == Decimal("0")


def test_success_history_affects_score():
    scorer = TaskScorer()

    good = scorer.score(
        make_task(
            success_rate=1.0
        )
    )

    bad = scorer.score(
        make_task(
            success_rate=0.0
        )
    )

    assert good.score > bad.score


def test_cooldown_affects_score():
    scorer = TaskScorer()

    short = scorer.score(
        make_task(
            cooldown_seconds=10
        )
    )

    long = scorer.score(
        make_task(
            cooldown_seconds=3600
        )
    )

    assert short.score > long.score


def test_rank_orders_tasks():
    scorer = TaskScorer()

    slow = make_task(
        reward="10",
        estimated_seconds=100,
    )

    fast = make_task(
        reward="100",
        estimated_seconds=10,
    )

    ranked = scorer.rank(
        [slow, fast]
    )

    assert (
        ranked[0].task.task_id
        == fast.task.task_id
    )

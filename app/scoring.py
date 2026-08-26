from __future__ import annotations

from decimal import Decimal

from .models import Task, TaskScore


class TaskScorer:
    """
    Menghitung skor prioritas sebuah task.

    Faktor:
    1. profitability = reward / estimated time
    2. cooldown_factor = semakin kecil cooldown, semakin tinggi
    3. success_factor = berdasarkan success history

    Scoring tidak melakukan eksekusi task.
    """

    def __init__(
        self,
        cooldown_weight: float = 0.15,
        success_weight: float = 0.25,
    ) -> None:
        self.cooldown_weight = Decimal(
            str(cooldown_weight)
        )

        self.success_weight = Decimal(
            str(success_weight)
        )

        if not (
            Decimal("0")
            <= self.cooldown_weight
            <= Decimal("1")
        ):
            raise ValueError(
                "cooldown_weight must be between 0 and 1"
            )

        if not (
            Decimal("0")
            <= self.success_weight
            <= Decimal("1")
        ):
            raise ValueError(
                "success_weight must be between 0 and 1"
            )

    @staticmethod
    def _clamp_success(
        success_rate: float,
    ) -> Decimal:
        """
        Batasi success rate ke 0.0 - 1.0.
        """
        value = Decimal(str(success_rate))

        return max(
            Decimal("0"),
            min(
                Decimal("1"),
                value,
            ),
        )

    @staticmethod
    def _profitability(
        task: Task,
    ) -> Decimal:
        """
        Reward per estimated second.
        """
        if task.estimated_seconds <= 0:
            return Decimal("0")

        return (
            task.reward
            / Decimal(task.estimated_seconds)
        )

    @staticmethod
    def _cooldown_factor(
        task: Task,
    ) -> Decimal:
        """
        Cooldown factor:

            1 / (1 + cooldown_hours)

        Contoh:
        cooldown 0 sec   -> 1.0
        cooldown 1 hour  -> 0.5
        cooldown 2 hours -> 0.333...
        """
        if task.cooldown_seconds <= 0:
            return Decimal("1")

        cooldown_hours = (
            Decimal(task.cooldown_seconds)
            / Decimal("3600")
        )

        return Decimal("1") / (
            Decimal("1") + cooldown_hours
        )

    def score(
        self,
        task: Task,
    ) -> TaskScore:
        """
        Hitung TaskScore untuk satu task.
        """

        profitability = self._profitability(task)

        if profitability <= 0:
            return TaskScore(
                task=task,
                profitability=Decimal("0"),
                cooldown_factor=Decimal("0"),
                success_factor=Decimal("0"),
                score=Decimal("0"),
            )

        cooldown_factor = self._cooldown_factor(task)

        success_factor = self._clamp_success(
            task.success_rate
        )

        # Cooldown adjustment.
        #
        # Weight 0.15 berarti cooldown hanya
        # mempengaruhi sebagian dari score.
        cooldown_multiplier = (
            Decimal("1")
            - self.cooldown_weight
            * (
                Decimal("1")
                - cooldown_factor
            )
        )

        # Success adjustment.
        #
        # Jika success_rate = 0:
        # multiplier = 1 - success_weight
        #
        # Jika success_rate = 1:
        # multiplier = 1
        success_multiplier = (
            Decimal("1")
            - self.success_weight
            + (
                self.success_weight
                * success_factor
            )
        )

        score = (
            profitability
            * cooldown_multiplier
            * success_multiplier
        )

        return TaskScore(
            task=task,
            profitability=profitability,
            cooldown_factor=cooldown_factor,
            success_factor=success_factor,
            score=score,
        )

    def rank(
        self,
        tasks: list[Task],
    ) -> list[TaskScore]:
        """
        Ranking task dari score terbesar ke terkecil.
        """
        scored = [
            self.score(task)
            for task in tasks
        ]

        return sorted(
            scored,
            key=lambda item: item.score,
            reverse=True,
        )

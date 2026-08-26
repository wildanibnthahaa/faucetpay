from app.config import load_config


def test_load_config(tmp_path):
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        """
database:
  path: "./data/test.db"

browser:
  enabled: false
  headless: true
  timeout_ms: 5000

discovery:
  enabled: true
  directory_url: "https://faucetpay.io/faucets"
  refresh_seconds: 120
  max_pages: 10

scoring:
  cooldown_weight: 0.2
  success_weight: 0.3
  minimum_score: 0.01

scheduler:
  enabled: true
  interval_seconds: 300
  max_tasks_per_cycle: 20
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.database.path.endswith("test.db")
    assert config.browser.timeout_ms == 5000
    assert config.discovery.max_pages == 10
    assert config.scheduler.interval_seconds == 300
    assert config.scoring.success_weight == 0.3

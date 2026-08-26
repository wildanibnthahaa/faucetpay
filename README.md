
<p align="center">
  <img src="docs/banner.svg" alt="FaucetPay Recovery Core" width="100%">
</p>

<h1 align="center">FaucetPay Recovery Core</h1>

<p align="center">
  Discovery, task analysis, persistence, scheduling, and monitoring
  for FaucetPay faucet-directory data.
</p>

<p align="center">
  <a href="#overview">Overview</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#installation">Installation</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#testing">Testing</a>
</p>

---

## Overview

FaucetPay Recovery Core is a Python application that provides a structured
foundation for collecting and analysing information from the FaucetPay
faucet directory.

The project is built around a modular architecture so discovery, data
storage, scoring, scheduling, and monitoring can be developed independently.

### Included

- Faucet directory discovery
- Faucet metadata collection
- Structured faucet and task models
- Profitability scoring
- Cooldown analysis
- Success-history analysis
- SQLite database
- Scheduled discovery cycles
- Task scheduling
- CLI dashboard
- Playwright browser integration
- YAML configuration
- Automated tests
- Docker support

---

## Architecture

```text
                    ┌─────────────────────────┐
                    │   FaucetPay Public      │
                    │      Directory          │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       Discovery         │
                    │        Playwright       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │         Models          │
                    │ Faucet / Task / Records │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
          ┌──────────────────┐      ┌──────────────────┐
          │      SQLite      │      │      Scoring      │
          │     Database     │      │      Engine       │
          └────────┬─────────┘      └────────┬─────────┘
                   │                         │
                   └────────────┬────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │    Scheduler / Bot      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      CLI Dashboard      │
                    └─────────────────────────┘
```

---

## Project Structure
```
faucetpay/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── bot.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── discovery.py
│   ├── scoring.py
│   ├── dashboard.py
│   ├── logging_config.py
│   └── utils.py
│
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_discovery.py
│   ├── test_scoring.py
│   └── test_bot.py
│
├── data/
├── logs/
├── docs/
│   └── banner.svg
│
├── config.yaml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── .env.example
└── README.md

```
---

## Installation
```
Requirements

Python 3.11 or newer

Git

curl

Playwright-compatible system dependencies
```

### Clone the repository
```
git clone https://github.com/wildanibnthahaa/faucetpay.git
cd faucetpay
```
### Install Python

If Python is not already installed:
```
curl -fsSL https://pyenv.run | bash

Restart your shell and install Python 3.11:

pyenv install 3.11
pyenv local 3.11
```
Verify:
```
python --version

Create a virtual environment

python -m venv .venv
source .venv/bin/activate
```
Install dependencies
```
pip install --upgrade pip
pip install -r requirements.txt
```
Install Playwright Chromium
```
playwright install chromium
```
For Linux servers, install the required browser dependencies:
```
playwright install-deps chromium
```

---

## Configuration

The application uses config.yaml for configuration.

### Example:
```
database:
  path: "./data/recovery.db"

browser:
  enabled: true
  headless: true
  timeout_ms: 30000

discovery:
  enabled: true
  directory_url: "https://faucetpay.io/faucets"
  refresh_seconds: 3600
  max_pages: 25

scoring:
  cooldown_weight: 0.15
  success_weight: 0.25
  minimum_score: 0.0

scheduler:
  enabled: true
  interval_seconds: 3600
  max_tasks_per_cycle: 50

The database is created automatically under the configured database path.
```

---

### Usage

Run a single discovery cycle

python -m app.bot --config config.yaml --once

This performs one discovery and scoring cycle and then exits.

Run the scheduler

python -m app.bot --config config.yaml

The scheduler periodically performs discovery and scoring according to the configured interval.

Open the dashboard

python -m app.dashboard --config config.yaml

The dashboard displays stored earnings information, faucet statistics, and recent records.


---

### Database

The application uses SQLite for local persistence.

The database stores:

Faucet information

Task information

Task status

Reward values

Estimated execution time

Cooldown values

Success history

Earning records

Timestamps

Error information


The default database location is:

data/recovery.db

SQLite WAL mode is enabled for improved reliability during normal application operation.


---

### Scoring

Tasks are ranked using several factors.

Profitability

profitability = reward / estimated_seconds

Higher reward relative to estimated time produces a higher base score.

Cooldown

Tasks with shorter cooldown periods receive a better cooldown factor.

Success history

Historical task success rates are incorporated into the final score.

The resulting score is used to rank available tasks before they enter the scheduler queue.


---

### Testing

Run the complete test suite:

pytest -q

Run a specific test module:

pytest tests/test_scoring.py -q

Run database tests:

pytest tests/test_database.py -q

Run discovery parser tests:

pytest tests/test_discovery.py -q

The test suite covers configuration loading, SQLite operations, discovery parsing, scoring behaviour, and scheduler logic.


---

### Docker

Build the containers:

docker compose build

Start the application:

docker compose up -d

View logs:

docker compose logs -f faucetpay-recovery

Run the test suite inside the container:

docker compose run --rm faucetpay-recovery pytest -q

The SQLite database and application logs are persisted through mounted volumes.


---

### Development

The repository is intended to be developed through GitHub forks.

To contribute changes:

1. Fork the repository.


2. Clone your fork.


3. Create a feature branch.


4. Make and test your changes.


5. Push the branch to your fork.


6. Open a pull request against the main repository.



Please keep changes focused and include tests when adding or modifying application behaviour.


---

### Configuration Files

File	Purpose

config.yaml	Application configuration
.env.example	Environment variable template
requirements.txt	Python dependencies
pytest.ini	Pytest configuration
Dockerfile	Container image
docker-compose.yml	Container orchestration



---

### License

This project is provided for educational and development purposes.

See the repository license for the applicable terms.

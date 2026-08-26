<p align="center">
  <img src="docs/banner.svg" alt="FaucetPay Recovery Core" width="100%">
</p>

<h1 align="center">FaucetPay Recovery Core</h1>

<p align="center">
  Read-only discovery, task analysis, persistence, scheduling,
  and observability for the public FaucetPay directory.
</p>

<p align="center">
  <a href="#overview">Overview</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#installation">Installation</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#testing">Testing</a> ·
  <a href="#roadmap">Roadmap</a>
</p>

---

## Overview

FaucetPay Recovery Core is a Python application designed to provide a structured,
auditable foundation for monitoring and analysing publicly available FaucetPay
faucet-directory information.

The project focuses on the non-destructive engineering layer:

- Public faucet discovery
- Faucet metadata collection
- Structured data models
- Task representation
- Profitability analysis
- Cooldown analysis
- Success-history analysis
- SQLite persistence
- Scheduled discovery cycles
- CLI dashboard
- Automated unit testing
- Playwright browser access
- YAML-based configuration
- Docker-ready deployment

The current implementation is intentionally **read-only**.

It does not submit faucet claims, complete offerwalls, solve CAPTCHAs,
bypass anti-bot systems, rotate residential proxies, manipulate browser
fingerprints, perform withdrawals, or automate multi-account farming.

This separation makes the discovery, scoring, persistence, and scheduling
layers easier to test, maintain, and audit.

---

## Project Status

| Component | Status |
|---|---|
| Data models | Complete |
| YAML configuration | Complete |
| SQLite database | Complete |
| Public directory discovery | Complete |
| Task scoring engine | Complete |
| Scheduler / orchestrator | Complete |
| CLI dashboard | Complete |
| Unit tests | Complete |
| Playwright integration | Complete |
| Docker configuration | Available |
| Automated claims | Not implemented |
| CAPTCHA automation | Not implemented |
| Proxy rotation | Not implemented |
| Fingerprint bypass | Not implemented |
| Automatic withdrawals | Not implemented |

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
          │      SQLite      │      │      Scoring     │
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






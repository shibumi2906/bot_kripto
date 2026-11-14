# Employer walkthrough

## 1. State the engineering problem

An LLM should not invent prices, risk or trade sizing. This project computes a versioned
technical report in ordinary Python, then optionally asks an LLM to explain that report.

## 2. Show offline determinism

Run twice:

```powershell
.\.venv\Scripts\python.exe -m app analyze --mode demo --balance 1000
```

Compare core.input_hash and core. They match. The mode and fixed as_of clearly identify
synthetic data. No account or API key is needed.

## 3. Open the core

Review app/domain/analysis.py: immutable input models, explicit time, validation,
indicators, risk components, decision gates and sizing. Explain that policy is heuristic;
this project demonstrates architecture and auditability, not validated trading alpha.

## 4. Show source integration

```powershell
.\.venv\Scripts\python.exe -m app analyze --mode live --symbol BTCUSDT
```

Inspect sources, sample_count, divergence_pct, collection_errors and rejected_sources.
Inspect risk.data_quality separately from risk.market and risk.position.
Current bid/ask appear under execution, with timestamp semantics and explicit blocks.
An unavailable provider is visible. One healthy source alone cannot produce a report.
Different live runs can differ because time and market inputs change.

## 5. Demonstrate the AI boundary

Inspect app/services/analyst.py and tests/test_analysis.py::test_ai_cannot_mutate_core_report.
The fake AI deliberately changes its copy; the core remains equal to the baseline.
This test proves data isolation, not the factual accuracy of generated prose.

If an OpenAI key and billing eligibility are configured, explicitly opt in:

```powershell
.\.venv\Scripts\python.exe -m app analyze --mode demo --explain
.\.venv\Scripts\python.exe -m app budget
```

Otherwise show the test without making a billable request.

## 6. Run verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Discuss missing/stale/NaN data, duplicate sources, cross-pair mixing, BUY sizing,
SELL interpretation, budget concurrency and HTTP validation.

## 7. Be explicit about scope

Working: deterministic technical analysis, three adapters, offline demo, CLI, local HTTP,
Telegram command entrypoint, optional AI adapter, persistent local token budget.

Not claimed: profitable strategy, model-calibrated risk, order execution, order-book
liquidity analysis, real news/on-chain integration, public authentication or completed billing.
Old SaaS code is disconnected from the demo API.

Useful follow-up discussion: replay storage, historical evaluation, threshold calibration,
provider resilience, security of a public deployment and user-level rate limits.

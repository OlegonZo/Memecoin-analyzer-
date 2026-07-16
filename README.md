# Memecoin Analyzer — Public Explainable Demo

[![tests](https://github.com/OlegonZo/Memecoin-analyzer-/actions/workflows/tests.yml/badge.svg)](https://github.com/OlegonZo/Memecoin-analyzer-/actions/workflows/tests.yml)

[Русская версия](README_RU.md)

A small, runnable Python portfolio project that demonstrates how I structure an
explainable wallet-accumulation signal: validate a token snapshot, remove dust,
weight wallet observations, calculate a transparent score, and apply market and
token-risk gates before raising a research priority.

This repository uses **synthetic token and wallet data only**. It contains no
wallet lists, credentials, API keys, production logs, live-order code, or
private calibration.

## What this demo shows

- typed, immutable `dataclass` input models with boundary validation;
- dust and negative-flow filtering before aggregation;
- quality-weighted accumulation across distinct wallets;
- liquidity, 24-hour volume, holder-concentration and authority checks;
- an explainable `WATCH` / `REJECT` result with every gate exposed;
- a dependency-free CLI, deterministic tests and continuous integration.

`WATCH` means “prioritize for further research.” It is **not** a buy signal,
financial advice, or an instruction to execute a trade.

## Evaluation flow

```text
synthetic JSON snapshot
        |
        v
model validation -> dust filter -> wallet weighting -> 0–100 score
                                                        |
                                                        v
                liquidity / volume / concentration / authority gates
                                                        |
                                                        v
                                  explainable WATCH or REJECT
```

The public score intentionally uses a simple composition:

- wallet breadth: up to 30 points;
- quality-weighted buying: up to 50 points;
- average wallet quality: up to 20 points.

All demo thresholds are readable in `EvaluationPolicy`. They were selected to
make the example easy to inspect and test; they are not production parameters.

## Run locally

Python 3.11 or newer is required. Runtime dependencies: none.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .

memecoin-analyzer-demo examples/synthetic_snapshot.json
```

Full machine-readable explanation:

```bash
memecoin-analyzer-demo examples/synthetic_snapshot.json --json
```

Run the tests:

```bash
python -m unittest discover -s tests -v
```

Example output:

```text
Token: DEMO
Decision: WATCH
Accumulation score: 87.77/100
Eligible wallets: 4
Dust/negative observations excluded: 2
...
[PASS] holder_concentration: 42.0% (required <= 65.0%)
```

## Repository layout

```text
src/memecoin_analyzer_demo/
  models.py       validated snapshot and policy models
  scoring.py      scoring, risk gates and explanation output
  cli.py          local JSON command-line interface
examples/
  synthetic_snapshot.json
tests/
  test_scoring.py
```

## Production boundary

My production research scanner is a separate private system. It includes data
collection, wallet research, calibrated discovery logic, persistence,
monitoring and Telegram delivery. Those components, real addresses and
historical datasets remain private for security and intellectual-property
reasons.

This public implementation is not copied production logic. It is a sanitized,
standalone demonstration of the engineering ideas I can discuss in an
interview: clear boundaries, deterministic evaluation, explainability, testing
and safe handling of sensitive data.

## Responsible use

Memecoins are highly risky. This project does not connect to a chain or an
exchange, does not place orders, and makes no claim of profitability. Any real
system requires independent validation, monitoring and risk controls.

## License

[MIT](LICENSE)


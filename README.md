# PumpFun DEX Sell Bot

Read-only / paper-mode monitor for one narrow strategy:

**Pump.fun → graduation/migration → PumpSwap pool → first verified matching AMM activity → PAPER SELL event**

This repository does **not** buy, sign, submit, or execute transactions. It has no private-key support.

## Architecture

```text
Pump.fun logsSubscribe
        ↓
Migration transaction
        ↓
Extract mint + PumpSwap pool
        ↓
Subscribe to pool logs
        ↓
Fetch matching transaction
        ↓
Validate pool + mint
        ↓
First matching AMM activity
        ↓
PAPER_SELL_RESULT
```

## Safety boundary

- `PAPER_MODE=true` is mandatory.
- No wallet/private key.
- No signing or transaction submission.
- No buy logic.
- No ML, optimization, backtesting, dashboard, or database.
- A timeout is reported as `NO_EXECUTABLE_ACTIVITY_TIMEOUT`, never as a failed pool.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

Set `SOLANA_RPC_URL` and `SOLANA_WS_URL` to your RPC provider. A Helius HTTPS/WSS endpoint or PublicNode endpoint can be used through environment variables; secrets are never committed.

## Program IDs

Pump.fun: `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

PumpSwap AMM: `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`

## States

`WAITING_FOR_GRADUATION → GRADUATION_DETECTED → POOL_FOUND → MONITORING_POOL → EXECUTABLE_ACTIVITY_DETECTED → PAPER_SELL_READY → PAPER_SELL_RESULT`

Terminal states: `NO_POOL_FOUND`, `NO_EXECUTABLE_ACTIVITY_TIMEOUT`, `PARSE_ERROR`, `RPC_ERROR`.

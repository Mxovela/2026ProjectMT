# MT5 Adaptive Forex Trading Bot (Python)

This repository contains a production-oriented scaffold for an **automated forex trading bot** designed for **MetaTrader 5 (MT5)** using Python.

It is built to:
- Operate on **M5 or M15** timeframes.
- Target a practical activity range of roughly **10–30 trades/day** (market dependent).
- Focus on **risk-adjusted execution** instead of random high-frequency entries.
- Adapt position sizing and aggressiveness to changing market regimes (trend vs. range and volatility changes).

> ⚠️ Trading is risky. No strategy can guarantee profits. Use this first on a demo account and perform robust forward testing.

## Strategy overview

The default strategy combines:
- **Trend filter**: Fast/slow EMA alignment.
- **Momentum confirmation**: RSI and ADX thresholds.
- **Volatility-aware exits**: Stop-loss/take-profit based on ATR multiples.
- **Regime adaptation**:
  - Lower risk in high-volatility or weak-trend conditions.
  - Slightly higher risk in strong-trend, normal-volatility conditions.

## Risk management implemented

- Fixed fractional risk per trade (e.g., `0.5%`) with dynamic scaling.
- Daily hard loss cap (e.g., `2.5%`) to halt trading for the day.
- Max concurrent open positions.
- Cooldown between entries per symbol.
- Spread filter to avoid poor fills.

## Project structure

- `bot/config.py` – strategy and runtime configuration.
- `bot/mt5_client.py` – MT5 connection + data/order helpers.
- `bot/strategy.py` – signal generation and regime classification.
- `bot/risk.py` – position sizing and daily guardrails.
- `bot/main.py` – bot loop.

## Quick start

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure MT5 terminal is installed and logged in (or pass login credentials via config).

3. Update `bot/config.py` defaults for your broker/symbols/risk appetite.

4. Run:

```bash
python -m bot.main
```

## Notes on 10–30 trades/day target

Trade frequency is controlled by:
- timeframe (M5 typically higher activity than M15),
- `entry_cooldown_minutes`,
- indicator thresholds (ADX/RSI/EMA alignment),
- market session and volatility.

If you need a stricter 10–30 range, tune thresholds and cooldown while preserving risk constraints.

## Next steps before live deployment

- Add broker-specific lot-step validation and min stop distance checks.
- Add persistent trade journal + analytics dashboard.
- Backtest over at least 2–3 years and perform walk-forward testing.
- Deploy with watchdog/service supervision and alerting.

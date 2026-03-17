from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MT5Credentials:
    login: Optional[int] = None
    password: Optional[str] = None
    server: Optional[str] = None


@dataclass
class BotConfig:
    symbols: List[str] = field(default_factory=lambda: ["EURUSD", "GBPUSD", "USDJPY"])
    timeframe: str = "M5"  # M5 or M15
    lookback_bars: int = 500
    poll_seconds: int = 20

    # Strategy parameters
    ema_fast_period: int = 21
    ema_slow_period: int = 55
    rsi_period: int = 14
    adx_period: int = 14
    atr_period: int = 14

    adx_trend_threshold: float = 20.0
    rsi_long_threshold: float = 55.0
    rsi_short_threshold: float = 45.0

    # Risk settings
    risk_per_trade_pct: float = 0.5
    max_daily_loss_pct: float = 2.5
    max_positions_total: int = 5
    max_spread_points: int = 30

    # Trade management
    stop_atr_multiple: float = 1.5
    take_profit_rr: float = 1.8
    entry_cooldown_minutes: int = 15

    # Adaptive behavior
    high_volatility_atr_ratio: float = 1.5
    low_trend_adx_threshold: float = 18.0
    high_trend_adx_threshold: float = 28.0
    min_risk_multiplier: float = 0.5
    max_risk_multiplier: float = 1.2

    mt5_credentials: MT5Credentials = field(default_factory=MT5Credentials)
    magic_number: int = 260317
    slippage_points: int = 20

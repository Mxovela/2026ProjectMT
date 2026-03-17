from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Signal:
    side: str  # "BUY", "SELL", "FLAT"
    atr: float
    adx: float
    regime: str


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    roll_up = pd.Series(up, index=series.index).rolling(period).mean()
    roll_down = pd.Series(down, index=series.index).rolling(period).mean()
    rs = roll_up / roll_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def _adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    atr = _atr(df, period)
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(period).sum() / atr.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(period).sum() / atr.replace(0, np.nan)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
    return dx.rolling(period).mean()


def build_signal(df: pd.DataFrame, cfg) -> Signal:
    work = df.copy()
    work["ema_fast"] = work["close"].ewm(span=cfg.ema_fast_period, adjust=False).mean()
    work["ema_slow"] = work["close"].ewm(span=cfg.ema_slow_period, adjust=False).mean()
    work["rsi"] = _rsi(work["close"], cfg.rsi_period)
    work["atr"] = _atr(work, cfg.atr_period)
    work["adx"] = _adx(work, cfg.adx_period)

    row = work.iloc[-1]
    atr_value = float(row["atr"])
    adx_value = float(row["adx"])

    atr_baseline = float(work["atr"].tail(100).mean()) if len(work) >= 100 else float(work["atr"].mean())
    atr_ratio = atr_value / atr_baseline if atr_baseline and not np.isnan(atr_baseline) else 1.0

    regime = "range"
    if adx_value >= cfg.high_trend_adx_threshold and atr_ratio < cfg.high_volatility_atr_ratio:
        regime = "strong_trend"
    elif adx_value >= cfg.adx_trend_threshold:
        regime = "trend"
    elif atr_ratio >= cfg.high_volatility_atr_ratio:
        regime = "volatile"

    long_ok = (
        row["ema_fast"] > row["ema_slow"]
        and row["rsi"] >= cfg.rsi_long_threshold
        and row["adx"] >= cfg.adx_trend_threshold
    )
    short_ok = (
        row["ema_fast"] < row["ema_slow"]
        and row["rsi"] <= cfg.rsi_short_threshold
        and row["adx"] >= cfg.adx_trend_threshold
    )

    if long_ok:
        side = "BUY"
    elif short_ok:
        side = "SELL"
    else:
        side = "FLAT"

    return Signal(side=side, atr=atr_value, adx=adx_value, regime=regime)

import time
from datetime import datetime, timedelta

from .config import BotConfig
from .mt5_client import MT5Client
from .risk import RiskManager
from .strategy import build_signal


def _calc_sl_tp(side: str, entry: float, atr: float, point: float, cfg):
    stop_distance = max(atr * cfg.stop_atr_multiple, point * 20)
    if side == "BUY":
        sl = entry - stop_distance
        tp = entry + (stop_distance * cfg.take_profit_rr)
    else:
        sl = entry + stop_distance
        tp = entry - (stop_distance * cfg.take_profit_rr)
    return sl, tp, stop_distance


def run_bot() -> None:
    cfg = BotConfig()
    mt5 = MT5Client(cfg)
    risk = RiskManager(cfg)
    last_trade_at = {symbol: datetime.min for symbol in cfg.symbols}

    mt5.initialize()
    print("Bot started")

    try:
        while True:
            equity = mt5.account_equity()
            if not risk.can_trade_today(equity):
                print("Daily loss limit reached; sleeping...")
                time.sleep(cfg.poll_seconds)
                continue

            if mt5.open_positions_count() >= cfg.max_positions_total:
                time.sleep(cfg.poll_seconds)
                continue

            for symbol in cfg.symbols:
                if datetime.utcnow() - last_trade_at[symbol] < timedelta(minutes=cfg.entry_cooldown_minutes):
                    continue

                if mt5.spread_points(symbol) > cfg.max_spread_points:
                    continue

                data = mt5.get_rates(symbol, cfg.timeframe, cfg.lookback_bars)
                signal = build_signal(data, cfg)
                if signal.side == "FLAT":
                    continue

                info = mt5.symbol_info(symbol)
                tick = mt5.symbol_tick(symbol)
                if info is None or tick is None:
                    continue

                entry = tick.ask if signal.side == "BUY" else tick.bid
                sl, tp, stop_distance_price = _calc_sl_tp(signal.side, entry, signal.atr, info.point, cfg)
                stop_distance_points = stop_distance_price / info.point

                lots = risk.position_size_lots(
                    equity=equity,
                    stop_distance_points=stop_distance_points,
                    point_value_per_lot=mt5.point_value_per_lot(symbol),
                    regime=signal.regime,
                    adx=signal.adx,
                )
                if lots <= 0:
                    continue

                mt5.place_order(symbol, signal.side, lots, sl, tp)
                last_trade_at[symbol] = datetime.utcnow()
                print(
                    f"{datetime.utcnow().isoformat()} | {symbol} {signal.side} lots={lots} "
                    f"regime={signal.regime} adx={signal.adx:.2f}"
                )

            time.sleep(cfg.poll_seconds)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    run_bot()

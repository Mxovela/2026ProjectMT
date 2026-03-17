from datetime import datetime

import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError as exc:  # pragma: no cover
    mt5 = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


TIMEFRAME_MAP = {
    "M5": mt5.TIMEFRAME_M5 if mt5 else None,
    "M15": mt5.TIMEFRAME_M15 if mt5 else None,
}


class MT5Client:
    def __init__(self, cfg):
        self.cfg = cfg

    def initialize(self) -> None:
        if mt5 is None:
            raise RuntimeError(f"MetaTrader5 module not installed: {IMPORT_ERROR}")

        creds = self.cfg.mt5_credentials
        if creds.login and creds.password and creds.server:
            ok = mt5.initialize(login=creds.login, password=creds.password, server=creds.server)
        else:
            ok = mt5.initialize()

        if not ok:
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    def shutdown(self) -> None:
        if mt5:
            mt5.shutdown()

    def account_equity(self) -> float:
        info = mt5.account_info()
        if info is None:
            raise RuntimeError(f"account_info failed: {mt5.last_error()}")
        return float(info.equity)

    def open_positions_count(self) -> int:
        pos = mt5.positions_get()
        return len(pos) if pos else 0

    def get_rates(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        tf = TIMEFRAME_MAP[timeframe]
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"No rates for {symbol}: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df

    def spread_points(self, symbol: str) -> int:
        tick = mt5.symbol_info_tick(symbol)
        info = mt5.symbol_info(symbol)
        if tick is None or info is None:
            return 99999
        return int((tick.ask - tick.bid) / info.point)

    def point_value_per_lot(self, symbol: str) -> float:
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"symbol_info unavailable for {symbol}")
        # Approximation: contract_size * point
        return float(info.trade_contract_size * info.point)

    def place_order(self, symbol: str, side: str, volume: float, sl: float, tp: float) -> None:
        tick = mt5.symbol_info_tick(symbol)
        info = mt5.symbol_info(symbol)
        if tick is None or info is None:
            raise RuntimeError(f"tick/symbol unavailable for {symbol}")

        price = tick.ask if side == "BUY" else tick.bid
        order_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": self.cfg.slippage_points,
            "magic": self.cfg.magic_number,
            "comment": f"adaptive_bot_{datetime.utcnow().isoformat()}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"order_send failed for {symbol}: {result}")

    def symbol_info(self, symbol: str):
        return mt5.symbol_info(symbol)

    def symbol_tick(self, symbol: str):
        return mt5.symbol_info_tick(symbol)

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RiskState:
    day_start_equity: float
    trading_day: str


class RiskManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.state = None

    def _ensure_day_state(self, equity: float) -> None:
        now_day = datetime.utcnow().strftime("%Y-%m-%d")
        if self.state is None or self.state.trading_day != now_day:
            self.state = RiskState(day_start_equity=equity, trading_day=now_day)

    def daily_loss_pct(self, equity: float) -> float:
        self._ensure_day_state(equity)
        assert self.state is not None
        pnl = equity - self.state.day_start_equity
        return (pnl / self.state.day_start_equity) * 100

    def can_trade_today(self, equity: float) -> bool:
        return self.daily_loss_pct(equity) > -self.cfg.max_daily_loss_pct

    def risk_multiplier_for_regime(self, regime: str, adx: float) -> float:
        mult = 1.0
        if regime == "strong_trend":
            mult = 1.1
        elif regime == "trend":
            mult = 1.0
        elif regime == "volatile":
            mult = 0.7
        elif regime == "range":
            mult = 0.6

        if adx < self.cfg.low_trend_adx_threshold:
            mult *= 0.9

        return max(self.cfg.min_risk_multiplier, min(self.cfg.max_risk_multiplier, mult))

    def position_size_lots(
        self,
        equity: float,
        stop_distance_points: float,
        point_value_per_lot: float,
        regime: str,
        adx: float,
    ) -> float:
        if stop_distance_points <= 0 or point_value_per_lot <= 0:
            return 0.0

        base_risk_amount = equity * (self.cfg.risk_per_trade_pct / 100)
        adjusted_risk_amount = base_risk_amount * self.risk_multiplier_for_regime(regime, adx)
        lots = adjusted_risk_amount / (stop_distance_points * point_value_per_lot)

        return max(0.01, round(lots, 2))

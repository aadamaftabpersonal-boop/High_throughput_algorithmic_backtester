# portfolio.py
"""
Day 3: Portfolio and order abstraction — tracks cash, positions, and fills
as a strategy trades through historical bars.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Order:
    ticker: str
    quantity: int          # positive = buy, negative = sell
    timestamp: datetime


@dataclass
class Fill:
    ticker: str
    quantity: int
    price: float            # actual execution price, after slippage
    timestamp: datetime
    commission: float = 0.0


class Portfolio:
    """
    Tracks cash and positions. Orders submitted during `on_bar` are filled
    at the NEXT bar's open — never the current bar's close — because in
    reality you can't know a bar closed until it's over, so trading on
    today's close is a form of look-ahead bias.
    """

    def __init__(self, starting_cash: float, slippage_bps: float = 5.0, commission_per_share: float = 0.0):
        self.cash = starting_cash
        self.positions: dict[str, int] = {}       # ticker -> quantity held
        self.fills: list[Fill] = []
        self.pending_orders: list[Order] = []
        self.slippage_bps = slippage_bps            # basis points, e.g. 5 = 0.05%
        self.commission_per_share = commission_per_share
        self.equity_curve: list[tuple[datetime, float]] = []

    def submit_order(self, ticker: str, quantity: int, timestamp: datetime):
        """Called by a strategy during on_bar(). Does NOT execute immediately."""
        self.pending_orders.append(Order(ticker=ticker, quantity=quantity, timestamp=timestamp))

    def _apply_slippage(self, price: float, quantity: int) -> float:
        """Buys fill slightly worse (higher) than quoted price; sells slightly worse (lower)."""
        direction = 1 if quantity > 0 else -1
        return price * (1 + direction * self.slippage_bps / 10_000)

    def process_pending_orders(self, next_bar_open: float, ticker: str, timestamp: datetime):
        """
        Called once per bar, BEFORE the strategy sees the new bar. Fills
        yesterday's (or last bar's) orders at this bar's open price.
        """
        still_pending = []
        for order in self.pending_orders:
            if order.ticker != ticker:
                still_pending.append(order)
                continue

            fill_price = self._apply_slippage(next_bar_open, order.quantity)
            cost = fill_price * order.quantity
            commission = abs(order.quantity) * self.commission_per_share

            if order.quantity > 0 and (cost + commission) > self.cash:
                # Not enough cash — order simply doesn't fill. No margin/debt
                # for now; add short-selling / margin logic later if needed.
                continue

            self.cash -= (cost + commission)
            self.positions[ticker] = self.positions.get(ticker, 0) + order.quantity
            self.fills.append(Fill(
                ticker=ticker, quantity=order.quantity, price=fill_price,
                timestamp=timestamp, commission=commission
            ))

        self.pending_orders = still_pending

    def mark_to_market(self, ticker: str, current_price: float, timestamp: datetime):
        """Record total portfolio value (cash + position value) at this point in time."""
        position_value = self.positions.get(ticker, 0) * current_price
        total_equity = self.cash + position_value
        self.equity_curve.append((timestamp, total_equity))
        return total_equity
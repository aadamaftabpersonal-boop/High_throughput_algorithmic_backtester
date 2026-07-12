# strategy.py
"""
Day 3: Strategy interface. A strategy only ever sees the current bar and
the portfolio — it cannot see future bars, which is the core discipline
that prevents look-ahead bias.
"""
from abc import ABC, abstractmethod
import pandas as pd
from src.portfolio import Portfolio


class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bar: pd.Series, portfolio: Portfolio) -> None:
        """
        Called once per historical bar, in chronological order.
        `bar` has: datetime, Open, High, Low, Close, Volume, ticker.
        Call `portfolio.submit_order(...)` to trade — it fills at the
        NEXT bar's open, not this bar's close.
        """
        raise NotImplementedError
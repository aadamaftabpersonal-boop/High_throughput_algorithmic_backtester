# strategies/moving_average_crossover.py
"""
Day 4: Simplest possible strategy to validate the interface design.
Buy when short MA crosses above long MA, sell when it crosses back below.
"""
import pandas as pd
from strategy import Strategy
from portfolio import Portfolio


class MovingAverageCrossover(Strategy):
    def __init__(self, ticker: str, short_window: int = 20, long_window: int = 50, shares: int = 10):
        self.ticker = ticker
        self.short_window = short_window
        self.long_window = long_window
        self.shares = shares
        self.price_history: list[float] = []
        self.position_open = False

    def on_bar(self, bar: pd.Series, portfolio: Portfolio) -> None:
        self.price_history.append(bar["Close"])

        if len(self.price_history) < self.long_window:
            return  # not enough history yet to compute the long MA

        short_ma = sum(self.price_history[-self.short_window:]) / self.short_window
        long_ma = sum(self.price_history[-self.long_window:]) / self.long_window

        if short_ma > long_ma and not self.position_open:
            portfolio.submit_order(self.ticker, self.shares, bar["datetime"])
            self.position_open = True
        elif short_ma < long_ma and self.position_open:
            portfolio.submit_order(self.ticker, -self.shares, bar["datetime"])
            self.position_open = False
# strategies/test_strategies.py
"""
Day 4: Minimal strategies that exist only to sanity-check the backtest engine.
Not meant to be "good" strategies — meant to have known, predictable outcomes.
"""
import pandas as pd
from strategy import Strategy
from portfolio import Portfolio


class BuyAndHold(Strategy):
    """Buy once on the very first bar, then do nothing else."""
    def __init__(self, ticker: str, shares: int = 10):
        self.ticker = ticker
        self.shares = shares
        self.bought = False

    def on_bar(self, bar: pd.Series, portfolio: Portfolio) -> None:
        if not self.bought:
            portfolio.submit_order(self.ticker, self.shares, bar["datetime"])
            self.bought = True


class NoOp(Strategy):
    """Never trades. Equity should stay exactly at starting cash."""
    def __init__(self, ticker: str):
        self.ticker = ticker

    def on_bar(self, bar: pd.Series, portfolio: Portfolio) -> None:
        pass
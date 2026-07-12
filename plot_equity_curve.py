# plot_equity_curve.py
"""Day 5: Visual sanity check + reusable for Week 4 demo."""
import matplotlib.pyplot as plt
import pandas as pd
from backtest import run_backtest
from strategies.test_strategies import BuyAndHold

portfolio = run_backtest("AAPL", BuyAndHold, starting_cash=100_000.0, shares=10)
df = pd.DataFrame(portfolio.equity_curve, columns=["datetime", "equity"])

plt.figure(figsize=(12, 5))
plt.plot(df["datetime"], df["equity"])
plt.title("AAPL Buy-and-Hold Equity Curve")
plt.xlabel("Date")
plt.ylabel("Portfolio Equity ($)")
plt.tight_layout()
plt.savefig("equity_curve_check.png")
print("Saved plot to equity_curve_check.png")
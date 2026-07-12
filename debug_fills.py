# debug_fills.py
"""Quick inspection: eyeball early fills to check for whipsaw vs a bug."""
from backtest import run_backtest
from strategies.moving_average_crossover import MovingAverageCrossover

portfolio = run_backtest("AAPL", MovingAverageCrossover, starting_cash=100_000.0,
                          short_window=20, long_window=50, shares=10)

for fill in portfolio.fills[:20]:
    print(f"{fill.timestamp} | qty={fill.quantity:+d} | price=${fill.price:.2f}")
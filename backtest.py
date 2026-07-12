# backtest.py
"""
Day 4: Naive single-threaded backtest loop — ties data, strategy, and
portfolio together. This is what weeks 2-3 will sandbox and parallelize.
"""
import pandas as pd
from pathlib import Path
from portfolio import Portfolio
from strategies.moving_average_crossover import MovingAverageCrossover


def run_backtest(ticker: str, strategy_cls, starting_cash: float = 100_000.0, **strategy_kwargs):
    df = pd.read_parquet(Path("data/raw") / f"{ticker}_clean.parquet")
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    portfolio = Portfolio(starting_cash=starting_cash)
    strategy = strategy_cls(ticker=ticker, **strategy_kwargs)

    for i in range(len(df) - 1):
        if i % 200_000 == 0:
            print(f"  progress: {i:,} / {len(df):,} rows ({i / len(df) * 100:.1f}%)")
        bar = df.iloc[i]
        next_bar = df.iloc[i + 1]

        # 1. Fill any orders from the PREVIOUS bar, at THIS bar's open.
        #    (Orders submitted while looking at bar i fill at bar i's open —
        #    meaning strategy decisions made on bar i-1 execute here.)
        portfolio.process_pending_orders(next_bar_open=bar["Open"], ticker=ticker, timestamp=bar["datetime"])

        # 2. Mark portfolio value using this bar's close.
        portfolio.mark_to_market(ticker=ticker, current_price=bar["Close"], timestamp=bar["datetime"])

        # 3. NOW let the strategy see this bar and decide. Any order it
        #    submits will fill at the NEXT bar's open (see step 1, next loop).
        strategy.on_bar(bar, portfolio)

    return portfolio


if __name__ == "__main__":
    portfolio = run_backtest("AAPL", MovingAverageCrossover, short_window=20, long_window=50, shares=10)

    equity_df = pd.DataFrame(portfolio.equity_curve, columns=["datetime", "equity"])
    print(f"Starting cash: $100,000.00")
    print(f"Ending equity: ${equity_df['equity'].iloc[-1]:,.2f}")
    print(f"Total fills: {len(portfolio.fills)}")
    print(equity_df.tail())
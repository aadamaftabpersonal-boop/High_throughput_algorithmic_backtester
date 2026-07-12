# test_backtest.py
"""
Day 5: Formal test suite — pytest instead of eyeballed print statements.
Run with: pytest test_backtest.py -v
"""
import pytest
import pandas as pd
from pathlib import Path
from backtest import run_backtest
from strategies.test_strategies import BuyAndHold, NoOp

STARTING_CASH = 100_000.0
TICKERS = ["AAPL", "SPY", "RBLX"]  # now covers all three, not just AAPL


@pytest.mark.parametrize("ticker", TICKERS)
def test_no_op_stays_flat(ticker):
    portfolio = run_backtest(ticker, NoOp, starting_cash=STARTING_CASH)
    final_equity = portfolio.equity_curve[-1][1]
    assert abs(final_equity - STARTING_CASH) < 0.01, \
        f"{ticker}: equity moved from {STARTING_CASH} to {final_equity} with zero trades"


@pytest.mark.parametrize("ticker", TICKERS)
def test_buy_and_hold_tracks_price(ticker):
    shares = 10
    portfolio = run_backtest(ticker, BuyAndHold, starting_cash=STARTING_CASH, shares=shares)

    df = pd.read_parquet(Path("data/raw") / f"{ticker}_clean.parquet")
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    first_price = df.iloc[0]["Open"]
    last_price = df.iloc[-1]["Close"]
    expected_equity = (STARTING_CASH - shares * first_price) + shares * last_price
    final_equity = portfolio.equity_curve[-1][1]

    diff_pct = abs(final_equity - expected_equity) / expected_equity * 100
    assert diff_pct < 1.0, \
        f"{ticker}: buy-and-hold off by {diff_pct:.3f}%, expected ~{expected_equity:.2f}, got {final_equity:.2f}"


@pytest.mark.parametrize("ticker", TICKERS)
def test_no_look_ahead_bias(ticker):
    """
    Fills should only ever happen at a bar's Open — never at that same
    bar's Close or High/Low. If a fill price exactly equals a Close price
    that isn't also the next bar's Open, something is trading on
    information it shouldn't have.
    """
    portfolio = run_backtest(ticker, BuyAndHold, starting_cash=STARTING_CASH, shares=10)
    df = pd.read_parquet(Path("data/raw") / f"{ticker}_clean.parquet")
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    open_prices = set(df["Open"].round(4))
    for fill in portfolio.fills:
        print("Doing")
        # fill price includes slippage, so check it's close to *some* Open, not an exact Close
        base_price = fill.price / (1 + 5.0 / 10_000)  # reverse the slippage adjustment
        assert any(abs(base_price - o) < 0.01 for o in open_prices), \
            f"{ticker}: fill at {fill.price} doesn't correspond to any bar's Open price"
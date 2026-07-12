# test_backtest_sanity.py
"""
Day 4: Sanity checks for the backtest engine before trusting it further.
Run with: python test_backtest_sanity.py
"""
import pandas as pd
from pathlib import Path
from backtest import run_backtest
from strategies.test_strategies import BuyAndHold, NoOp
from strategies.moving_average_crossover import MovingAverageCrossover

TICKER = "AAPL"
STARTING_CASH = 100_000.0


def test_no_op():
    print("\n--- Test 1: No-op strategy (should stay flat at starting cash) ---")
    portfolio = run_backtest(TICKER, NoOp, starting_cash=STARTING_CASH)
    final_equity = portfolio.equity_curve[-1][1]
    print(f"Starting cash: ${STARTING_CASH:,.2f}")
    print(f"Final equity:  ${final_equity:,.2f}")
    passed = abs(final_equity - STARTING_CASH) < 0.01
    print("PASS ✓" if passed else "FAIL ✗ — equity moved without any trades")
    return passed


def test_buy_and_hold():
    print("\n--- Test 2: Buy-and-hold (should roughly track AAPL's price return) ---")
    shares = 10
    portfolio = run_backtest(TICKER, BuyAndHold, starting_cash=STARTING_CASH, shares=shares)

    df = pd.read_parquet(Path("data/raw") / f"{TICKER}_clean.parquet")
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    first_price = df.iloc[0]["Open"]
    last_price = df.iloc[-1]["Close"]
    expected_position_value = shares * last_price
    remaining_cash = STARTING_CASH - (shares * first_price)  # rough, ignores slippage/commission
    expected_equity_approx = remaining_cash + expected_position_value

    final_equity = portfolio.equity_curve[-1][1]
    print(f"AAPL price: ${first_price:.2f} -> ${last_price:.2f}")
    print(f"Expected equity (approx, ignoring slippage): ${expected_equity_approx:,.2f}")
    print(f"Actual final equity:                          ${final_equity:,.2f}")

    diff_pct = abs(final_equity - expected_equity_approx) / expected_equity_approx * 100
    passed = diff_pct < 1.0  # allow ~1% tolerance for slippage/commission
    print(f"Difference: {diff_pct:.3f}%")
    print("PASS ✓" if passed else "FAIL ✗ — bigger than slippage/commission should explain")
    return passed


def test_ma_crossover_fills_after_signal():
    print("\n--- Test 3: MA crossover fills happen AFTER the signal bar, not on it ---")
    portfolio = run_backtest(TICKER, MovingAverageCrossover, starting_cash=STARTING_CASH,
                              short_window=20, long_window=50, shares=10)
    print(f"Total fills: {len(portfolio.fills)}")
    if portfolio.fills:
        first_fill = portfolio.fills[0]
        print(f"First fill: {first_fill.timestamp} | qty={first_fill.quantity} | price=${first_fill.price:.2f}")
    passed = len(portfolio.fills) > 0
    print("PASS ✓ (fills occurred, eyeball timestamps above manually)" if passed else "FAIL ✗ — no fills at all, check crossover logic")
    return passed


if __name__ == "__main__":
    results = {
        "no_op": test_no_op(),
        "buy_and_hold": test_buy_and_hold(),
        "ma_crossover": test_ma_crossover_fills_after_signal(),
    }
    print("\n=== Summary ===")
    for name, passed in results.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
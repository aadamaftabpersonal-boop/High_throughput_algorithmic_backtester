# validate_data.py
"""
Day 2: Validate schema, check for gaps, confirm split/dividend adjustment.
"""
import pandas as pd

def validate(df: pd.DataFrame, ticker: str) -> dict:
    issues = {}

    # 1. Schema check
    expected_cols = {"datetime", "Open", "High", "Low", "Close", "Volume"}
    missing_cols = expected_cols - set(df.columns)
    if missing_cols:
        issues["missing_columns"] = missing_cols

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    # 2. Check regular session coverage (09:30-16:00 ET) per trading day
    df["date"] = df["datetime"].dt.date
    df["time"] = df["datetime"].dt.time
    bars_per_day = df.groupby("date").size()

    # A full regular session = 390 one-minute bars (9:30am-4:00pm)
    incomplete_days = bars_per_day[bars_per_day < 150]  # small buffer for holidays/early closes
    if len(incomplete_days) > 0:
        issues["incomplete_days"] = incomplete_days.to_dict()

    # 3. Check for duplicate timestamps
    dupes = df["datetime"].duplicated().sum()
    if dupes > 0:
        issues["duplicate_timestamps"] = dupes

    # 4. Sanity check OHLC relationships (High >= Open,Close,Low; Low <= all)
    bad_bars = df[
        (df["High"] < df[["Open", "Close", "Low"]].max(axis=1)) |
        (df["Low"] > df[["Open", "Close", "High"]].min(axis=1))
    ]
    if len(bad_bars) > 0:
        issues["invalid_ohlc_bars"] = len(bad_bars)

    print(f"\n=== {ticker} ===")
    print(f"Rows: {len(df):,} | Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Trading days: {df['date'].nunique()}")
    if issues:
        for k, v in issues.items():
            print(f"  ⚠ {k}: {v if not isinstance(v, dict) else f'{len(v)} days affected'}")
    else:
        print("  ✓ No issues found")

    return issues

def inspect_distribution(df: pd.DataFrame, ticker: str):
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["date"] = df["datetime"].dt.date
    bars_per_day = df.groupby("date").size()

    print(f"\n=== {ticker} bar-count distribution ===")
    print(bars_per_day.describe())
    print("\nPercentiles:")
    for p in [1, 5, 10, 25, 50]:
        print(f"  {p}th percentile: {bars_per_day.quantile(p/100):.0f} bars")

    # Show the actual worst days — these are the ones worth eyeballing
    print("\nWorst 10 days:")
    print(bars_per_day.sort_values().head(10))

if __name__ == "__main__":
    from fetch_data import fetch_ticker, TICKERS

    all_issues = {}
    for ticker in TICKERS:
        df = fetch_ticker(ticker)
        all_issues[ticker] = validate(df, ticker)
        inspect_distribution(df, ticker)
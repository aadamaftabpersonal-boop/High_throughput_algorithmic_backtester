# validate_data.py
"""
Day 2: Validate schema, distinguish expected partial days from real anomalies,
and persist a clean per-ticker report other days can build on.
"""
import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw")
REPORT_DIR = Path("data/validation")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# U.S. market early-close dates (1pm ET close, ~210 min session instead of 390).
# Day before Thanksgiving, day before/on Christmas, July 3rd (when it's the
# trading day before July 4th). Not exhaustive across 20+ years — extend as
# you find more early-close-shaped days (190-210 bars, day before a holiday).
KNOWN_EARLY_CLOSES = {
    "2013-07-03", "2013-11-29",
    "2015-11-27", "2015-12-24",
    "2016-11-25",
    "2017-07-03",
    "2019-07-03", "2019-12-24",
    "2022-11-25",
    "2023-07-03", "2023-11-24",
    "2024-06-18", "2024-07-03", "2024-11-29", "2024-12-24",
    "2025-07-03", "2025-11-28", "2025-12-24",
}

# Below this bar count, a day isn't just "zero-volume minutes dropped" —
# something real is likely missing. Tuned from AAPL/SPY distributions: normal
# days cluster 345-390, real early closes bottom out ~190-200, so anything
# well under that has a different cause.
ANOMALY_THRESHOLD = 150

# First trading day for tickers that IPO'd/listed mid-history — naturally partial.
KNOWN_LISTING_DAYS = {
    "RBLX": "2021-03-10",
}


def classify_day(date_str: str, bar_count: int, ticker: str) -> str:
    """
    Zero-volume minutes are excluded by the data source, so bar counts vary
    continuously below 390 even on completely normal trading days (median
    is ~380-383 for liquid names). That's not a gap — only three things are
    actually worth flagging: known early-close sessions, a ticker's first
    (partial) listing day, and days far enough below normal variation to
    suggest something genuinely went missing.
    """
    if date_str in KNOWN_EARLY_CLOSES:
        return "early_close"
    if KNOWN_LISTING_DAYS.get(ticker) == date_str:
        return "listing_day"
    if bar_count < ANOMALY_THRESHOLD:
        return "anomaly"
    return "normal"


def validate(df: pd.DataFrame, ticker: str) -> dict:
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")
    df["date"] = df["datetime"].dt.date.astype(str)

    issues = {}

    # Schema check
    expected_cols = {"datetime", "Open", "High", "Low", "Close", "Volume"}
    missing_cols = expected_cols - set(df.columns)
    if missing_cols:
        issues["missing_columns"] = list(missing_cols)

    # Duplicate timestamps
    dupes = int(df["datetime"].duplicated().sum())
    if dupes > 0:
        issues["duplicate_timestamps"] = dupes

    # Invalid OHLC relationships (High must be >= Open/Close/Low, Low <= all)
    bad_bars = df[
        (df["High"] < df[["Open", "Close", "Low"]].max(axis=1)) |
        (df["Low"] > df[["Open", "Close", "High"]].min(axis=1))
    ]
    if len(bad_bars) > 0:
        issues["invalid_ohlc_bars"] = int(len(bad_bars))

    # Classify every trading day
    bars_per_day = df.groupby("date").size()
    classifications = {
        date: classify_day(date, count, ticker)
        for date, count in bars_per_day.items()
    }
    class_counts = pd.Series(classifications.values()).value_counts().to_dict()

    anomaly_dates = sorted(d for d, c in classifications.items() if c == "anomaly")

    report = {
        "ticker": ticker,
        "row_count": int(len(df)),
        "date_range": [df["date"].min(), df["date"].max()],
        "trading_days": int(df["date"].nunique()),
        "day_classification_counts": class_counts,
        "anomaly_dates": anomaly_dates,
        "issues": issues,
    }

    print(f"\n=== {ticker} ===")
    print(f"Rows: {report['row_count']:,} | Trading days: {report['trading_days']}")
    print(f"Day classification: {class_counts}")
    if anomaly_dates:
        print(f"  ⚠ {len(anomaly_dates)} anomaly day(s): {anomaly_dates}")
    else:
        print("  ✓ no anomalies")
    if issues:
        print(f"  ⚠ other issues: {issues}")

    return report


if __name__ == "__main__":
    from fetch_data import TICKERS

    all_reports = {}
    for ticker in TICKERS:
        local_path = DATA_DIR / f"{ticker}_clean.parquet"
        df = pd.read_parquet(local_path)
        all_reports[ticker] = validate(df, ticker)

    report_path = REPORT_DIR / "day2_validation_report.json"
    report_path.write_text(json.dumps(all_reports, indent=2))
    print(f"\nSaved report to {report_path}")
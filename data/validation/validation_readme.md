# Data Validation Notes — Day 2

## Source
1-minute OHLCV bars, HF Data Library ("clean" version), tickers: AAPL, SPY, RBLX.
Full history through 2026-07-10. See `fetch_data.py` for retrieval.

## Known data characteristics

**Zero-volume minutes are dropped by the source.**
Any minute with no executed trades is excluded from the file rather than
written as a zero-volume row. This means daily bar counts vary continuously
below the full 390-bar session (9:30am–4:00pm ET) even on completely normal
trading days — median bar count is ~380-383 for AAPL/SPY, lower and more
variable (~330 median) for the less-liquid RBLX. This is expected behavior,
not missing data, and required re-deriving the validation threshold rather
than using a fixed "under 390 = incomplete" check.

**Split/dividend adjustment confirmed.**
Prices are split-adjusted (e.g., AAPL trading at ~$0.23 in Dec 2002 reflects
multiple subsequent splits applied backward). This is the correct behavior
for backtesting — unadjusted data would show fake price discontinuities on
split dates.

## Day classification (validate_data.py)

Every trading day is labeled one of:
- `normal` — ordinary session, bar count reflects zero-volume-minute exclusion
- `early_close` — known 1pm ET close (day before Thanksgiving/Christmas, July 3rd);
  hardcoded list in `KNOWN_EARLY_CLOSES`, not exhaustive across all 20+ years —
  extend as needed if a `normal`-looking day turns out to bottom out ~190-210 bars
- `listing_day` — ticker's first trading day (RBLX: 2021-03-10, partial session
  due to direct listing, trading didn't start at market open)
- `anomaly` — bar count under 150, no known explanation

## Findings

| Ticker | Trading days | Normal | Early close | Listing day | Anomaly |
|--------|-------------|--------|-------------|-------------|---------|
| AAPL   | 5,918       | 5,899  | 18          | –           | 1       |
| SPY    | 5,917       | 5,898  | 18          | –           | 1       |
| RBLX   | 1,338       | 1,326  | 10          | 1           | 1       |

**One unexplained anomaly: 2024-12-23**, present in both AAPL and SPY (RBLX too),
with bar counts in the 42–53 range vs. an expected ~380+. Not a scheduled
early-close date. Since it affects multiple tickers on the same date, likely
a provider-side issue (partial feed, late data, outage) rather than anything
ticker-specific. Not further investigated — see decision below.

## Decision: handling 2024-12-23

[FILL IN — e.g.: "Excluded from all backtests via a hardcoded skip list.
One day out of ~5,900 trading days; negligible impact on results, not worth
the engineering cost of handling partial-day sessions gracefully for a single
known outlier."]

## Other validation checks (all clean)
- Schema: no missing expected columns (datetime, Open, High, Low, Close, Volume)
- No duplicate timestamps found
- No invalid OHLC bars (High/Low relationships all consistent)

## Files
- `fetch_data.py` — retrieval + local Parquet caching
- `validate_data.py` — validation + day classification, outputs `day2_validation_report.json`
- `day2_validation_report.json` — per-ticker classification results, consumed by later backtest logic
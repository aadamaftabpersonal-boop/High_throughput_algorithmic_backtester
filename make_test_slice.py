import pandas as pd

df = pd.read_parquet("data/raw/AAPL_clean.parquet")
df["datetime"] = pd.to_datetime(df["datetime"])
df_small = df[(df["datetime"] >= "2022-01-01") & (df["datetime"] < "2022-06-01")]
df_small.to_parquet("data/raw/AAPL_TEST_clean.parquet")
print(f"Wrote {len(df_small):,} rows to AAPL_TEST_clean.parquet")
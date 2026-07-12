"""
Runs INSIDE the container. Reads bar data from a mounted file, runs the
strategy's on_bar() for every bar, and writes ORDER INTENTS (not real fills)
to a results file. Never touches the real Portfolio.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")

import pandas as pd
from user_strategy import UserStrategy


class OrderIntentRecorder:
    def __init__(self):
        self.intents = []

    def submit_order(self, ticker, quantity, timestamp):
        self.intents.append({
            "ticker": ticker,
            "quantity": quantity,
            "timestamp": str(timestamp),
        })


def main():
    df = pd.read_parquet("/data/input.parquet")
    print(f"DEBUG columns: {list(df.columns)}", flush=True)
    print(f"DEBUG shape: {df.shape}", flush=True)

    if df.empty:
        raise RuntimeError("Input data is empty — check the volume mount path on the host side.")

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    recorder = OrderIntentRecorder()
    strategy = UserStrategy(ticker="AAPL")

    for i in range(len(df)):
        strategy.on_bar(df.iloc[i], recorder)

    Path("/output/intents.json").write_text(json.dumps(recorder.intents))
    print(f"Processed {len(df)} bars, recorded {len(recorder.intents)} order intents", flush=True)


if __name__ == "__main__":
    main()
#importing api key from .env
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("HFD_API_KEY")

if not API_KEY:
    raise RuntimeError("Set HFD_API_KEY in your .env file before running.")

"""
Day1: Pull minute wise OHLCV data from HF data library, load and inspect
"""
import pandas as pd 
import requests
from pathlib import Path 

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)
TICKERS = ["AAPL", "SPY", "RBLX"]

# Updated to the correct official API subdomain and version path
BASE_URL = "https://api.hfdatalibrary.com/v1"

def fetch_ticker(ticker: str, version: str = "clean") -> pd.DataFrame:
    """
    Fetch 1-minute OHLCV bars for a ticker.
    Downloads the full historical compressed Parquet bundle directly to disk.
    """
    local_path = DATA_DIR / f"{ticker}_{version}.parquet"
    
    # Check if we already have the data locally
    if local_path.exists():
        print(f"{ticker}: using cached file")
        return pd.read_parquet(local_path)
    
    # Construct the correct path-based endpoint URL
    url = f"{BASE_URL}/download/{ticker}"
    
    headers = {
        "X-API-Key": API_KEY
    }
    params = {
        "version": version
    }
    
    print(f"Fetching {ticker} from HF Data Library...")
    resp = requests.get(url, headers=headers, params=params)
    
    # If the token is invalid or the URL changed, this prints the exact server error message
    if resp.status_code != 200:
        print(f"Error Details: {resp.text}")
        
    resp.raise_for_status()
    
    # Write raw Parquet bytes out to our local cache directory
    local_path.write_bytes(resp.content)
    
    df = pd.read_parquet(local_path)
    print(f"{ticker}: fetched {len(df):,} rows")
    return df

if __name__ == "__main__":
    for ticker in TICKERS:
        try:
            df = fetch_ticker(ticker)
            print("\n--- First 5 rows ---")
            print(df.head())
            print("\n--- Data Schema ---")
            print(df.dtypes)
            print("=" * 40)
        except Exception as e:
            print(f"Failed to process {ticker}: {e}")
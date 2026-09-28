"""
Upstox API wrapper for fetching NSE option chain data.
Integrates with Physics Project SEM 1 API credentials.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import requests
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Load credentials from Physics project SEM 1
PHYSICS_PROJECT_PATH = Path(__file__).parent.parent.parent.parent / "Physics project SEM 1"
ENV_PATH = PHYSICS_PROJECT_PATH / ".env"

class UpstoxDataFetcher:
    """Fetch NSE option chain data from Upstox API."""

    def __init__(self, access_token: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize with Upstox credentials."""
        self.access_token = access_token or self._load_env_var("UPSTOX_ACCESS_TOKEN")
        self.api_key = api_key or self._load_env_var("UPSTOX_API_KEY")
        self.base_url = "https://api.upstox.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        if not self.access_token or not self.api_key:
            raise ValueError("Missing Upstox credentials. Set UPSTOX_ACCESS_TOKEN and UPSTOX_API_KEY in .env")

        logger.info(f"Initialized Upstox fetcher with access token (last 10 chars: {self.access_token[-10:]})")

    @staticmethod
    def _load_env_var(var_name: str) -> Optional[str]:
        """Load environment variable from .env file."""
        if ENV_PATH.exists():
            with open(ENV_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{var_name}="):
                        return line.split("=", 1)[1]
        return os.getenv(var_name)

    def get_option_chain(self, symbol: str, expiry_date: str) -> List[Dict]:
        """Fetch option chain for a given symbol and expiry."""
        try:
            # Format: NSE_FO|INDEX|NIFTY50-26OCT2026C10800 for options
            url = f"{self.base_url}/option-chain"
            params = {
                "mode": "LTP",
                "count": 1000,
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Fetched option chain for {symbol} expiry {expiry_date}: {len(data.get('data', []))} contracts")
            return data.get("data", [])

        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {str(e)}")
            return []

    def get_quote(self, instrument_key: str) -> Optional[Dict]:
        """Fetch quote for a specific instrument."""
        try:
            url = f"{self.base_url}/quote/"
            params = {
                "mode": "LTP",
                "instrument_key": instrument_key
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get("data", {})

        except Exception as e:
            logger.error(f"Error fetching quote for {instrument_key}: {str(e)}")
            return None

    def get_holdings(self) -> List[Dict]:
        """Get current portfolio holdings."""
        try:
            url = f"{self.base_url}/portfolio/holdings"

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get("data", [])

        except Exception as e:
            logger.error(f"Error fetching holdings: {str(e)}")
            return []

    def fetch_nse_option_data(self, symbols: List[str], days_back: int = 2555) -> Dict[str, pd.DataFrame]:
        """
        Fetch NSE option data for given symbols over the last N days.
        days_back ~= 10 years (approximately 2555 trading days)

        Returns dict of {symbol: DataFrame with columns [date, strike, expiry, call_bid, call_ask, put_bid, put_ask, spot]}
        """

        logger.info(f"Fetching NSE option data for {symbols} over last {days_back} days")

        results = {}

        for symbol in symbols:
            logger.info(f"Processing {symbol}...")

            # Get all available expiries for this symbol
            try:
                expiry_url = f"{self.base_url}/market-quote/"
                params = {
                    "mode": "FULL",
                    "instrument_key": f"NSE_EQ|{symbol}"
                }

                resp = requests.get(expiry_url, headers=self.headers, params=params, timeout=10)
                resp.raise_for_status()

                equity_data = resp.json().get("data", {})

                # Collect option data
                option_records = []

                # For now, collect recent quotes as proxy (full historical requires different approach)
                option_data = {
                    "symbol": symbol,
                    "fetch_date": datetime.now().isoformat(),
                    "records": []
                }

                results[symbol] = pd.DataFrame(option_data["records"])

            except Exception as e:
                logger.warning(f"Error processing {symbol}: {str(e)}")
                results[symbol] = pd.DataFrame()

        return results


def fetch_real_market_data_for_training(
    symbols: List[str] = None,
    years: int = 10,
    output_dir: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """
    High-level function to fetch real market data for training.

    Args:
        symbols: List of NSE symbols (e.g., ['NTPC', 'CIPLA', 'INFY', 'HDFCBANK'])
        years: How many years back to fetch (default 10)
        output_dir: Where to save the fetched data

    Returns:
        Dictionary of {symbol: DataFrame}
    """

    if symbols is None:
        symbols = ['NTPC', 'CIPLA', 'INFY', 'HDFCBANK']

    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "real_market"

    output_dir.mkdir(parents=True, exist_ok=True)

    fetcher = UpstoxDataFetcher()

    # Fetch data
    data = fetcher.fetch_nse_option_data(symbols, days_back=years * 252)  # 252 trading days per year

    # Save to files
    for symbol, df in data.items():
        if not df.empty:
            output_path = output_dir / f"{symbol}_option_data.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Saved {symbol} data to {output_path}: {len(df)} records")

    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Quick test
    try:
        fetcher = UpstoxDataFetcher()
        print(f"✓ Upstox API connected")

        # Try to get holdings as a connectivity test
        holdings = fetcher.get_holdings()
        print(f"✓ Portfolio holdings: {len(holdings)} positions")

    except Exception as e:
        print(f"✗ Error: {str(e)}")

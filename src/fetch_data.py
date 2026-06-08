"""
Download daily price and volume data from CoinGecko API.
Computes log returns and saves individual CSV files to data/.
"""
from pycoingecko import CoinGeckoAPI
import pandas as pd
import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from config import ASSETS, DATA_FOLDER

cg = CoinGeckoAPI()

def fetch_all():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    for coin in ASSETS:
        print(f"Fetching {coin}...")
        data = cg.get_coin_market_chart_by_id(
            id=coin, vs_currency='usd', days='max'
        )
        prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        volumes = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
        df = prices.merge(volumes, on='timestamp')
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['date', 'price', 'volume']]
        df['log_return'] = np.log(df['price'] / df['price'].shift(1))
        df.to_csv(os.path.join(DATA_FOLDER, f'{coin}.csv'), index=False)
        print(f"  {coin} done — {len(df)} rows")

if __name__ == "__main__":
    fetch_all()

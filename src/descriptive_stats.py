"""
Table 5.1: Descriptive statistics of daily log returns.
"""
import pandas as pd
import numpy as np
from scipy import stats
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import ASSETS, LABELS, DATA_FOLDER, OUTPUT_FOLDER

results = []
for coin, label in zip(ASSETS, LABELS):
    df = pd.read_csv(os.path.join(DATA_FOLDER, f'{coin}.csv'), parse_dates=['date'])
    r = df['log_return'].dropna()
    results.append({
        'Asset': label,
        'Observations': len(r),
        'Start date': df['date'].min().strftime('%Y-%m-%d'),
        'End date': df['date'].max().strftime('%Y-%m-%d'),
        'Mean return (%)': round(r.mean() * 100, 4),
        'Std dev (%)': round(r.std() * 100, 4),
        'Min (%)': round(r.min() * 100, 4),
        'Max (%)': round(r.max() * 100, 4),
        'Skewness': round(stats.skew(r), 4),
        'Excess kurtosis': round(stats.kurtosis(r), 4),
    })

table = pd.DataFrame(results)
print(table.to_string(index=False))
table.to_csv(os.path.join(OUTPUT_FOLDER, 'table_5_1_descriptive_stats.csv'), index=False)
print(f'\nSaved to {OUTPUT_FOLDER}/table_5_1_descriptive_stats.csv')

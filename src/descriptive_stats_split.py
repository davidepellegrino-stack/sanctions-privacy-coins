"""
Table 5.2: Descriptive statistics split at Monero delisting (Feb 2024).
"""
import pandas as pd
import numpy as np
from scipy import stats
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import ASSETS, LABELS, DATA_FOLDER, OUTPUT_FOLDER, MONERO_DELISTING_DATE

results = []
for coin, label in zip(ASSETS, LABELS):
    df = pd.read_csv(os.path.join(DATA_FOLDER, f'{coin}.csv'), parse_dates=['date'])
    pre  = df[df['date'] < MONERO_DELISTING_DATE]['log_return'].dropna()
    post = df[df['date'] >= MONERO_DELISTING_DATE]['log_return'].dropna()
    for period, r in [('Pre-delisting', pre), ('Post-delisting', post)]:
        results.append({
            'Asset': label, 'Period': period, 'Obs.': len(r),
            'Mean (%)': round(r.mean() * 100, 4),
            'Std Dev (%)': round(r.std() * 100, 4),
            'Min (%)': round(r.min() * 100, 4),
            'Max (%)': round(r.max() * 100, 4),
            'Skewness': round(stats.skew(r), 4),
            'Ex. Kurtosis': round(stats.kurtosis(r), 4),
        })

table = pd.DataFrame(results)
print(table.to_string(index=False))
table.to_csv(os.path.join(OUTPUT_FOLDER, 'table_5_2_pre_post.csv'), index=False)
print('\nSaved.')

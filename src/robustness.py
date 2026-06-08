"""
Robustness checks:
  1. Ethereum placebo (transparent blockchain, should show no effect)
  2. Pre/post Monero delisting sample split (Feb 2024)
  3. High severity subsample (Severity = 3)
"""
import pandas as pd
import numpy as np
from scipy import stats
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import (EVENTS_FILE, DATA_FOLDER, OUTPUT_FOLDER,
                    ASSETS, LABELS, ESTIMATION_WINDOW, EVENT_WINDOWS,
                    TREATMENT, MONERO_DELISTING_DATE)

# ── LOAD DATA ─────────────────────────────────────────────────────────────
prices = {}
for asset, label in zip(ASSETS, LABELS):
    df = pd.read_csv(os.path.join(DATA_FOLDER, f"{asset}.csv"), parse_dates=['date'])
    df = df.set_index('date').sort_index()
    prices[label] = df['log_return']
returns = pd.DataFrame(prices)
benchmark_series = returns['BTC']

events_df = pd.read_excel(EVENTS_FILE, sheet_name="Events Table")
keep_mask = events_df['Keep in\nSample?'].astype(str).str.contains('KEEP', na=False)
exclude_mask = events_df['Keep in\nSample?'].astype(str).str.contains('EXCLUDE', na=False)
caution_mask = events_df['Keep in\nSample?'].astype(str).str.contains('CAUTION', na=False)
keep_mask = keep_mask & ~exclude_mask & ~caution_mask
events_df = events_df[keep_mask].copy()
events_df['Date'] = pd.to_datetime(events_df['Date'])
events_df = events_df.dropna(subset=['Date'])
esc_events = events_df[events_df['Direction'] == 'Escalation']

# ── HELPERS ───────────────────────────────────────────────────────────────
def get_AR_and_sigma(asset_label, event_date, window):
    asset_series = returns[asset_label]
    est_start = event_date + pd.Timedelta(days=ESTIMATION_WINDOW[0])
    est_end   = event_date + pd.Timedelta(days=ESTIMATION_WINDOW[1])
    evt_start = event_date + pd.Timedelta(days=window[0])
    evt_end   = event_date + pd.Timedelta(days=window[1])

    est_mask = (asset_series.index >= est_start) & (asset_series.index <= est_end)
    est_asset = asset_series[est_mask].dropna()
    est_bench = benchmark_series[est_mask].dropna()
    common = est_asset.index.intersection(est_bench.index)
    if len(common) < 60: return None, None

    ea, eb = est_asset[common].values, est_bench[common].values
    X = np.column_stack([np.ones(len(eb)), eb])
    bh, _, _, _ = np.linalg.lstsq(X, ea, rcond=None)
    alpha, beta = bh[0], bh[1]
    sigma = np.std(ea - (alpha + beta * eb), ddof=2)

    evt_mask = (asset_series.index >= evt_start) & (asset_series.index <= evt_end)
    evt_asset = asset_series[evt_mask].dropna()
    evt_bench = benchmark_series[evt_mask].dropna()
    common_e = evt_asset.index.intersection(evt_bench.index)
    if len(common_e) == 0: return None, None

    AR = evt_asset[common_e].values - (alpha + beta * evt_bench[common_e].values)
    return AR, sigma

def bmp_test(CARs_std):
    n = len(CARs_std)
    if n < 2: return np.nan, np.nan
    t = np.mean(CARs_std) / (np.std(CARs_std, ddof=1) / np.sqrt(n))
    p = 2 * (1 - stats.t.cdf(abs(t), df=n-1))
    return round(t, 4), round(p, 4)

def corrado_test(ARs_list):
    ranks = []
    for AR in ARs_list:
        if AR is None or len(AR) == 0: continue
        r = stats.rankdata(AR)
        ranks.append(r - (len(r)+1)/2)
    if len(ranks) < 2: return np.nan, np.nan
    ev = np.array([r[-1] for r in ranks])
    sk = np.sqrt(np.mean([np.var(r, ddof=1) for r in ranks]))
    if sk == 0: return np.nan, np.nan
    z = (np.mean(ev) / sk) / np.sqrt(len(ev))
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return round(z, 4), round(p, 4)

def stars(p):
    if pd.isna(p): return ""
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""

def run_tests(asset_list, events, label=""):
    rows = []
    for asset in asset_list:
        for window in EVENT_WINDOWS:
            ws = f"[{window[0]},{window[1]}]"
            CARs, CARs_std, ARs_list = [], [], []
            for _, ev in events.iterrows():
                AR, sigma = get_AR_and_sigma(asset, ev['Date'], window)
                if AR is None or sigma == 0: continue
                car = np.sum(AR)
                CARs.append(car * 100)
                CARs_std.append(car / (sigma * np.sqrt(len(AR))))
                ARs_list.append(AR)
            if len(CARs) < 2: continue
            bmp_t, bmp_p = bmp_test(np.array(CARs_std))
            cor_z, cor_p = corrado_test(ARs_list)
            rows.append({
                'Sample': label, 'Asset': asset, 'Window': ws,
                'N': len(CARs), 'Mean CAR': round(np.mean(CARs), 4),
                'BMP t': bmp_t, 'BMP p': bmp_p, 'BMP sig': stars(bmp_p),
                'Corrado z': cor_z, 'Corrado p': cor_p, 'Corrado sig': stars(cor_p),
            })
    return rows

# ── CHECK 1: PLACEBO (ETH) ───────────────────────────────────────────────
print("=" * 70)
print("ROBUSTNESS 1 — PLACEBO TEST (ETH as fake treatment)")
print("=" * 70)
placebo_rows = run_tests(['ETH'], esc_events, label="Placebo (ETH)")
for r in placebo_rows:
    print(f"ETH | {r['Window']:10s} | N={r['N']:2d} | Mean CAR={r['Mean CAR']:8.4f}% | "
          f"BMP t={r['BMP t']:6.3f}{r['BMP sig']:3s} | Corrado z={r['Corrado z']:6.3f}{r['Corrado sig']:3s}")

# ── CHECK 2: SAMPLE SPLIT ────────────────────────────────────────────────
print("\n" + "=" * 70)
print(f"ROBUSTNESS 2 — SAMPLE SPLIT at {MONERO_DELISTING_DATE}")
print("=" * 70)
split = pd.Timestamp(MONERO_DELISTING_DATE)
pre_events  = esc_events[esc_events['Date'] < split]
post_events = esc_events[esc_events['Date'] >= split]
print(f"Pre: {len(pre_events)} events | Post: {len(post_events)} events\n")

pre_rows  = run_tests(TREATMENT, pre_events,  label="Pre-delisting")
post_rows = run_tests(TREATMENT, post_events, label="Post-delisting")

for r in pre_rows:
    print(f"{r['Asset']:4s} | {r['Window']:10s} | N={r['N']:2d} | Mean CAR={r['Mean CAR']:8.4f}% | "
          f"BMP t={r['BMP t']:6.3f}{r['BMP sig']:3s}")
print()
for r in post_rows:
    print(f"{r['Asset']:4s} | {r['Window']:10s} | N={r['N']:2d} | Mean CAR={r['Mean CAR']:8.4f}% | "
          f"BMP t={r['BMP t']:6.3f}{r['BMP sig']:3s}")

# ── CHECK 3: HIGH SEVERITY ───────────────────────────────────────────────
print("\n" + "=" * 70)
print("ROBUSTNESS 3 — HIGH SEVERITY EVENTS ONLY (Severity = 3)")
print("=" * 70)
high_sev = esc_events[esc_events['Severity\n(1-3)'].astype(str) == '3']
print(f"High severity events: {len(high_sev)}\n")
sev_rows = run_tests(TREATMENT, high_sev, label="High severity")
for r in sev_rows:
    print(f"{r['Asset']:4s} | {r['Window']:10s} | N={r['N']:2d} | Mean CAR={r['Mean CAR']:8.4f}% | "
          f"BMP t={r['BMP t']:6.3f}{r['BMP sig']:3s}")

# ── SAVE ──────────────────────────────────────────────────────────────────
all_rows = placebo_rows + pre_rows + post_rows + sev_rows
pd.DataFrame(all_rows).to_csv(os.path.join(OUTPUT_FOLDER, "robustness_results.csv"), index=False)
print(f"\nSaved to: {OUTPUT_FOLDER}/robustness_results.csv")

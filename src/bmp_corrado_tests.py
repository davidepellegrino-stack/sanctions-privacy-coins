"""
BMP (Boehmer, Musumeci & Poulsen, 1991) and Corrado (1989) rank tests.
Reads event_study_CARs.csv and computes cross-sectional test statistics.
"""
import pandas as pd
import numpy as np
from scipy import stats
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import (EVENTS_FILE, DATA_FOLDER, OUTPUT_FOLDER,
                    ASSETS, LABELS, ESTIMATION_WINDOW, EVENT_WINDOWS,
                    TREATMENT, CONTROL)

RESULTS_FILE = os.path.join(OUTPUT_FOLDER, "event_study_CARs.csv")

results_df = pd.read_csv(RESULTS_FILE)
print(f"Loaded {len(results_df)} event-asset-window combinations\n")

# ── RELOAD PRICE DATA ────────────────────────────────────────────────────
prices = {}
for asset, label in zip(ASSETS, LABELS):
    df = pd.read_csv(os.path.join(DATA_FOLDER, f"{asset}.csv"), parse_dates=['date'])
    df = df.set_index('date').sort_index()
    prices[label] = df['log_return']
returns = pd.DataFrame(prices)
benchmark_series = returns['BTC']

# ── RELOAD EVENTS ─────────────────────────────────────────────────────────
events_df = pd.read_excel(EVENTS_FILE, sheet_name="Events Table")
keep_mask = events_df['Keep in\nSample?'].astype(str).str.contains('KEEP', na=False)
exclude_mask = events_df['Keep in\nSample?'].astype(str).str.contains('EXCLUDE', na=False)
caution_mask = events_df['Keep in\nSample?'].astype(str).str.contains('CAUTION', na=False)
keep_mask = keep_mask & ~exclude_mask & ~caution_mask
events_df = events_df[keep_mask].copy()
events_df['Date'] = pd.to_datetime(events_df['Date'])
events_df = events_df.dropna(subset=['Date'])

def get_ARs(asset_label, event_date, window):
    """Compute abnormal returns for a single (asset, event, window)."""
    asset_series = returns[asset_label]
    est_start = event_date + pd.Timedelta(days=ESTIMATION_WINDOW[0])
    est_end   = event_date + pd.Timedelta(days=ESTIMATION_WINDOW[1])
    evt_start = event_date + pd.Timedelta(days=window[0])
    evt_end   = event_date + pd.Timedelta(days=window[1])

    est_mask = (asset_series.index >= est_start) & (asset_series.index <= est_end)
    est_asset = asset_series[est_mask].dropna()
    est_bench = benchmark_series[est_mask].dropna()
    common_est = est_asset.index.intersection(est_bench.index)
    if len(common_est) < 60:
        return None, None

    ea, eb = est_asset[common_est].values, est_bench[common_est].values
    X = np.column_stack([np.ones(len(eb)), eb])
    beta_hat, _, _, _ = np.linalg.lstsq(X, ea, rcond=None)
    alpha, beta = beta_hat[0], beta_hat[1]
    sigma = np.std(ea - (alpha + beta * eb), ddof=2)

    evt_mask = (asset_series.index >= evt_start) & (asset_series.index <= evt_end)
    evt_asset = asset_series[evt_mask].dropna()
    evt_bench = benchmark_series[evt_mask].dropna()
    common_evt = evt_asset.index.intersection(evt_bench.index)
    if len(common_evt) == 0:
        return None, None

    AR = evt_asset[common_evt].values - (alpha + beta * evt_bench[common_evt].values)
    return AR, sigma

def bmp_test(CARs_std):
    """BMP cross-sectional t-test on standardised CARs."""
    n = len(CARs_std)
    if n < 2: return np.nan, np.nan
    t_stat = np.mean(CARs_std) / (np.std(CARs_std, ddof=1) / np.sqrt(n))
    p_val  = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))
    return round(t_stat, 4), round(p_val, 4)

def corrado_test(all_ARs_list):
    """Corrado (1989) non-parametric rank test."""
    ranks_list = []
    for ARs in all_ARs_list:
        if ARs is None or len(ARs) == 0: continue
        r = stats.rankdata(ARs)
        ranks_list.append(r - (len(r) + 1) / 2)
    if len(ranks_list) < 2: return np.nan, np.nan
    event_ranks = np.array([r[-1] for r in ranks_list])
    sigma_K = np.sqrt(np.mean([np.var(r, ddof=1) for r in ranks_list]))
    if sigma_K == 0: return np.nan, np.nan
    z_stat = (np.mean(event_ranks) / sigma_K) / np.sqrt(len(event_ranks))
    p_val  = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    return round(z_stat, 4), round(p_val, 4)

def stars(p):
    if pd.isna(p): return ""
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""

# ── MAIN LOOP ─────────────────────────────────────────────────────────────
print("Running BMP and Corrado tests...")
print("=" * 75)

output_rows = []
esc_events = events_df[events_df['Direction'] == 'Escalation']

for asset in TREATMENT + CONTROL:
    for window in EVENT_WINDOWS:
        window_str = f"[{window[0]},{window[1]}]"
        CARs, CARs_std, all_ARs_list = [], [], []

        for _, event in esc_events.iterrows():
            AR, sigma = get_ARs(asset, event['Date'], window)
            if AR is None or sigma == 0: continue
            car = np.sum(AR)
            CARs.append(car * 100)
            CARs_std.append(car / (sigma * np.sqrt(len(AR))))
            all_ARs_list.append(AR)

        if len(CARs) < 2: continue

        mean_CAR = round(np.mean(CARs), 4)
        bmp_t, bmp_p = bmp_test(np.array(CARs_std))
        corrado_z, corr_p = corrado_test(all_ARs_list)

        print(f"{asset:4s} | {window_str:10s} | N={len(CARs):2d} | "
              f"Mean CAR={mean_CAR:8.4f}% | "
              f"BMP t={bmp_t:6.3f}{stars(bmp_p):3s} (p={bmp_p:.3f}) | "
              f"Corrado z={corrado_z:6.3f}{stars(corr_p):3s} (p={corr_p:.3f})")

        output_rows.append({
            'Asset': asset, 'Group': 'Treatment' if asset in TREATMENT else 'Control',
            'Window': window_str, 'N events': len(CARs),
            'Mean CAR (%)': mean_CAR,
            'BMP t-stat': bmp_t, 'BMP p-value': bmp_p, 'BMP sig': stars(bmp_p),
            'Corrado z': corrado_z, 'Corrado p': corr_p, 'Corrado sig': stars(corr_p),
        })

print("=" * 75)
out_df = pd.DataFrame(output_rows)
out_df.to_csv(os.path.join(OUTPUT_FOLDER, "bmp_corrado_results.csv"), index=False)
print(f"\nSaved to: {OUTPUT_FOLDER}/bmp_corrado_results.csv")
print("\n*** = p<0.01  ** = p<0.05  * = p<0.10")

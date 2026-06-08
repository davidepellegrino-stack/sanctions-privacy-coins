"""
Event study: market model estimation and CAR computation.
Computes CARs for all (asset, event, window) combinations.
"""
import pandas as pd
import numpy as np
from scipy import stats
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import (EVENTS_FILE, DATA_FOLDER, OUTPUT_FOLDER,
                    ESTIMATION_WINDOW, EVENT_WINDOWS,
                    ASSETS, LABELS, BENCHMARK, TREATMENT, CONTROL)

# ── LOAD PRICE DATA ──────────────────────────────────────────────────────
print("Loading price data...")
prices = {}
for asset, label in zip(ASSETS, LABELS):
    df = pd.read_csv(os.path.join(DATA_FOLDER, f"{asset}.csv"), parse_dates=['date'])
    df = df.set_index('date').sort_index()
    prices[label] = df['log_return']

returns = pd.DataFrame(prices)
print(f"Price data loaded: {len(returns)} trading days")
print(f"Date range: {returns.index[0].date()} to {returns.index[-1].date()}\n")

# ── LOAD EVENTS ───────────────────────────────────────────────────────────
print("Loading events...")
events_df = pd.read_excel(EVENTS_FILE, sheet_name="Events Table")
keep_mask = events_df['Keep in\nSample?'].astype(str).str.contains('KEEP', na=False)
exclude_mask = events_df['Keep in\nSample?'].astype(str).str.contains('EXCLUDE', na=False)
caution_mask = events_df['Keep in\nSample?'].astype(str).str.contains('CAUTION', na=False)
keep_mask = keep_mask & ~exclude_mask & ~caution_mask
events_df = events_df[keep_mask].copy()
events_df['Date'] = pd.to_datetime(events_df['Date'])
events_df = events_df.dropna(subset=['Date'])
print(f"Events loaded: {len(events_df)} events after filtering\n")

# ── EVENT STUDY FUNCTION ──────────────────────────────────────────────────
def run_event_study(asset_returns, benchmark_returns, event_date, window):
    """
    Market model event study for a single (asset, event, window).
    R_i,t = alpha + beta * R_BTC,t + epsilon_t
    Returns dict with CAR, AR series, model params, or None.
    """
    est_start = event_date + pd.Timedelta(days=ESTIMATION_WINDOW[0])
    est_end   = event_date + pd.Timedelta(days=ESTIMATION_WINDOW[1])
    evt_start = event_date + pd.Timedelta(days=window[0])
    evt_end   = event_date + pd.Timedelta(days=window[1])

    # Estimation window
    est_mask = (asset_returns.index >= est_start) & (asset_returns.index <= est_end)
    est_asset = asset_returns[est_mask].dropna()
    est_bench = benchmark_returns[est_mask].dropna()
    common_est = est_asset.index.intersection(est_bench.index)
    if len(common_est) < 60:
        return None

    # OLS market model
    X = np.column_stack([np.ones(len(common_est)), est_bench[common_est].values])
    y = est_asset[common_est].values
    beta_hat, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    alpha, beta = beta_hat[0], beta_hat[1]

    y_hat = alpha + beta * est_bench[common_est].values
    residuals = y - y_hat
    sigma = np.std(residuals, ddof=2)

    # Event window
    evt_mask = (asset_returns.index >= evt_start) & (asset_returns.index <= evt_end)
    evt_asset = asset_returns[evt_mask].dropna()
    evt_bench = benchmark_returns[evt_mask].dropna()
    common_evt = evt_asset.index.intersection(evt_bench.index)
    if len(common_evt) == 0:
        return None

    expected = alpha + beta * evt_bench[common_evt].values
    AR = evt_asset[common_evt].values - expected
    CAR = np.sum(AR)

    return {
        'CAR': CAR, 'AR': AR,
        'alpha': alpha, 'beta': beta, 'sigma': sigma,
        'n_est': len(common_est), 'n_evt': len(common_evt),
    }

# ── MAIN LOOP ─────────────────────────────────────────────────────────────
print("Running event study...")
results = []
benchmark_series = returns['BTC']

for _, event in events_df.iterrows():
    event_id   = event['Event ID']
    event_date = event['Date']
    direction  = event['Direction']
    severity   = event['Severity\n(1-3)']
    country    = event['Country']
    relief     = event['Relief\nDummy']

    for asset in TREATMENT + CONTROL:
        for window in EVENT_WINDOWS:
            res = run_event_study(returns[asset], benchmark_series, event_date, window)
            if res is None:
                continue
            results.append({
                'event_id': event_id, 'event_date': event_date.date(),
                'country': country, 'direction': direction,
                'severity': severity, 'relief': relief,
                'asset': asset,
                'group': 'Treatment' if asset in TREATMENT else 'Control',
                'window': f"[{window[0]},{window[1]}]",
                'CAR': round(res['CAR'] * 100, 4),
                'alpha': round(res['alpha'], 6), 'beta': round(res['beta'], 4),
                'sigma': round(res['sigma'], 6),
                'n_est': res['n_est'], 'n_evt': res['n_evt'],
            })

results_df = pd.DataFrame(results)
results_df.to_csv(os.path.join(OUTPUT_FOLDER, "event_study_CARs.csv"), index=False)
print(f"Done. {len(results_df)} combinations computed.")

print("\n=== QUICK SUMMARY: Mean CAR by Asset and Window ===")
summary = results_df[results_df['direction'] == 'Escalation'].groupby(
    ['asset', 'window'])['CAR'].agg(['mean', 'count']).round(4)
print(summary)
print("\nRun bmp_corrado_tests.py for significance tests.")

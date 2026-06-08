"""
Difference-in-differences on trading volumes.
log(Volume_i,t) = alpha + beta(Privacy_i x Post_t) + asset FE + date FE + eps
Standard errors clustered at the asset level.
"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import (EVENTS_FILE, DATA_FOLDER, OUTPUT_FOLDER,
                    ASSETS, LABELS, DID_WINDOW_DAYS)

# ── LOAD PANEL ────────────────────────────────────────────────────────────
print("Loading price data...")
dfs = []
for asset, label in zip(ASSETS, LABELS):
    df = pd.read_csv(os.path.join(DATA_FOLDER, f"{asset}.csv"), parse_dates=['date'])
    df['asset'] = label
    df['privacy'] = 1 if label in ['XMR', 'ZEC', 'DASH'] else 0
    dfs.append(df)
panel = pd.concat(dfs, ignore_index=True).sort_values(['asset', 'date']).reset_index(drop=True)
print(f"Panel loaded: {len(panel)} asset-day observations\n")

# ── LOAD EVENTS ───────────────────────────────────────────────────────────
events_df = pd.read_excel(EVENTS_FILE, sheet_name="Events Table")
keep_mask = events_df['Keep in\nSample?'].astype(str).str.contains('KEEP', na=False)
exclude_mask = events_df['Keep in\nSample?'].astype(str).str.contains('EXCLUDE', na=False)
caution_mask = events_df['Keep in\nSample?'].astype(str).str.contains('CAUTION', na=False)
keep_mask = keep_mask & ~exclude_mask & ~caution_mask
events_df = events_df[keep_mask].copy()
events_df['Date'] = pd.to_datetime(events_df['Date'])
esc_events = events_df[events_df['Direction'] == 'Escalation']['Date'].tolist()
print(f"Escalation events: {len(esc_events)}\n")

# ── EVENT-LEVEL DiD ──────────────────────────────────────────────────────
print("Running DiD regressions for each event...")
print("=" * 70)
all_results = []

for event_date in esc_events:
    start = event_date - pd.Timedelta(days=DID_WINDOW_DAYS)
    end   = event_date + pd.Timedelta(days=DID_WINDOW_DAYS)
    sub = panel[(panel['date'] >= start) & (panel['date'] <= end)].copy()
    if len(sub) < 100: continue

    sub['post'] = (sub['date'] > event_date).astype(int)
    sub['did']  = sub['privacy'] * sub['post']
    sub['log_volume'] = np.log(sub['volume'].clip(lower=1))

    try:
        model = smf.ols(
            'log_volume ~ did + privacy + post + C(asset) + C(date)', data=sub
        ).fit(cov_type='cluster', cov_kwds={'groups': sub['asset']})

        all_results.append({
            'event_date': event_date.date(),
            'n_obs': len(sub),
            'beta_did': round(model.params['did'], 4),
            'se_did':   round(model.bse['did'], 4),
            't_stat':   round(model.tvalues['did'], 4),
            'p_value':  round(model.pvalues['did'], 4),
            'sig': '***' if model.pvalues['did'] < 0.01 else
                   '**'  if model.pvalues['did'] < 0.05 else
                   '*'   if model.pvalues['did'] < 0.10 else ''
        })
    except Exception:
        continue

res_df = pd.DataFrame(all_results)
print(f"\nCompleted {len(res_df)} event-level DiD regressions\n")
print(res_df[['event_date','beta_did','se_did','t_stat','p_value','sig']].to_string(index=False))

# ── POOLED DiD ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("POOLED DiD — All escalation events combined")
print("=" * 70)

pooled_dfs = []
for event_date in esc_events:
    start = event_date - pd.Timedelta(days=DID_WINDOW_DAYS)
    end   = event_date + pd.Timedelta(days=DID_WINDOW_DAYS)
    sub = panel[(panel['date'] >= start) & (panel['date'] <= end)].copy()
    if len(sub) < 100: continue
    sub['post'] = (sub['date'] > event_date).astype(int)
    sub['did']  = sub['privacy'] * sub['post']
    sub['log_volume'] = np.log(sub['volume'].clip(lower=1))
    sub['event_id'] = event_date.strftime('%Y-%m-%d')
    pooled_dfs.append(sub)

pooled = pd.concat(pooled_dfs, ignore_index=True)
print(f"Pooled panel: {len(pooled):,} observations")

try:
    pooled_model = smf.ols(
        'log_volume ~ did + privacy + post + C(asset) + C(event_id)', data=pooled
    ).fit(cov_type='cluster', cov_kwds={'groups': pooled['asset']})
    print(f"\nPooled beta:    {pooled_model.params['did']:.4f}")
    print(f"SE:             {pooled_model.bse['did']:.4f}")
    print(f"t-stat:         {pooled_model.tvalues['did']:.4f}")
    print(f"p-value:        {pooled_model.pvalues['did']:.4f}")
    print(f"R-squared:      {pooled_model.rsquared:.4f}")
except Exception as e:
    print(f"Pooled model error: {e}")

res_df.to_csv(os.path.join(OUTPUT_FOLDER, "did_results.csv"), index=False)
print(f"\nSaved to: {OUTPUT_FOLDER}/did_results.csv")

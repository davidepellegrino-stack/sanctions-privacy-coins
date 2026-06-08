# Sanctions and Privacy Coins

**Do major economic sanctions announcements generate abnormal returns or abnormal trading volumes in privacy-focused cryptocurrencies?**

M1 thesis in Financial Economics, Université Paris 1 Panthéon-Sorbonne. Supervised by Prof. Olena Havrylchyk.

## Research Design

Privacy coins (Monero, Zcash, Dash) offer protocol-level transaction anonymity. This study tests whether 37 sanctions announcements (2014-2026) produce measurable price or volume reactions in these assets, using Bitcoin and Ethereum as transparent-blockchain controls.

### Event Study
- Market model: `R_i,t = α + β R_BTC,t + ε`
- Estimation window: [-200, -20] trading days
- Event windows: [-1,+1], [-5,+5], [-5,+30]
- Inference: BMP test (Boehmer, Musumeci & Poulsen, 1991) and Corrado rank test (1989)

### Difference-in-Differences on Volumes
- `log(Volume_i,t) = α + β(Privacy × Post) + asset FE + date FE + ε`
- Window: ±180 calendar days per event
- Standard errors clustered at the asset level

### Robustness
- Ethereum placebo test
- Pre/post Monero delisting sample split (Feb 2024)
- Severity-3 subsample (14 largest events)

## Key Findings

1. **No significant abnormal returns.** Largest estimate: XMR at -4.01% over [-5,+30], BMP t = -1.55, p = 0.134.
2. **Privacy coin volumes fall after major sanctions.** DiD: EU 6th package β = -1.00 (p < 0.001); NK UNSC failure β = -1.03 (p < 0.001).
3. **Substitution hypothesis.** Evasion demand flows to stablecoins (~84% of illicit crypto by 2025), not privacy coins.

## Repository Structure

```
├── data/                       # Price CSVs + sanctions events Excel
│   └── sanctions_events.xlsx   # 37 events with dates, severity, direction
├── src/
│   ├── config.py               # All parameters and paths
│   ├── fetch_data.py           # Download from CoinGecko API
│   ├── descriptive_stats.py    # Table 5.1: full-sample statistics
│   ├── descriptive_stats_split.py  # Table 5.2: pre/post delisting
│   ├── event_study.py          # Market model + CAR computation
│   ├── bmp_corrado_tests.py    # BMP and Corrado significance tests
│   ├── did_regression.py       # DiD on volumes (event-level + pooled)
│   └── robustness.py           # Placebo, sample split, severity checks
├── outputs/                    # Generated tables (CSV)
├── requirements.txt
└── README.md
```

## Usage

```bash
pip install -r requirements.txt

# 1. Fetch price data
python src/fetch_data.py

# 2. Descriptive statistics
python src/descriptive_stats.py
python src/descriptive_stats_split.py

# 3. Event study
python src/event_study.py
python src/bmp_corrado_tests.py

# 4. Difference-in-differences
python src/did_regression.py

# 5. Robustness checks
python src/robustness.py
```

**Note:** Place your `sanctions_events.xlsx` file in `data/` before running. The events Excel file uses columns: `Date`, `Event ID`, `Direction`, `Severity (1-3)`, `Country`, `Relief Dummy`, `Keep in Sample?`.

## Data Sources
- **Prices and volumes:** CoinGecko API (free)
- **Sanctions events:** Hand-collected from OFAC SDN List, EU Official Journal, UN Security Council resolutions

## Citation

Pellegrino, D. (2026). *Sanctions and Privacy Coins: Do Major Economic Sanctions Announcements Generate Abnormal Returns and Abnormal Trading Volumes in Privacy-Focused Cryptocurrencies?* M1 Thesis, Université Paris 1 Panthéon-Sorbonne.

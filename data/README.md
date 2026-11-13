# Sanctions events dataset

Hand-collected by Davide Pellegrino for the M1 thesis (Université Paris 1 Panthéon-Sorbonne), from the OFAC SDN list and press releases, executive orders, the EU Official Journal, UN Security Council resolutions and court rulings.

- `sanctions_events.xlsx`: the file the scripts read (sheet "Events Table"), plus the sheets "Legend & Methodology" and "Data Quality Notes".
- `sanctions_events.csv`: the same "Events Table", for viewing on GitHub and loading without Excel.

## Coverage

42 events, 2014-2026: Russia (14), Iran (13), North Korea (6), Venezuela (5) and crypto-specific actions (4: Tornado Cash sanction, Samourai Wallet arrests, Fifth Circuit ruling, Tornado Cash delisting). 37 are escalations and 5 are relief events (expected sign reversed).

## Columns

| Column | Meaning |
|---|---|
| Event ID | R = Russia, I = Iran, NK = North Korea, V = Venezuela, C = crypto-specific |
| Date | Announcement or signing date (YYYY-MM-DD); day 0 of the event window |
| Country | Targeted country, or N/A for crypto-specific actions |
| Authority | OFAC, EU, UN, G7, DOJ/FinCEN, US Courts |
| Event Description | What was decided, with the legal reference |
| Type | Targeted, sectoral, comprehensive, secondary, energy, banking, crypto/mixer, relief |
| Severity (1-3) | 1 = low, 2 = medium, 3 = high: scope, multilateral coordination, economic impact |
| Direction | Escalation or De-escalation |
| Relief Dummy | 1 for de-escalation events |
| Cluster Flag | Proximity to other events; rule: exclude if within 10 days of another event |
| Keep in Sample? | KEEP / EXCLUDE / CAUTION, with the reason |
| Notes / Crypto Relevance | Expected effect, confounders and data-quality caveats |

## Sample used by the code

The scripts keep rows whose "Keep in Sample?" contains KEEP and neither EXCLUDE nor CAUTION. That gives the thesis estimation sample: 37 events (32 escalations, 5 de-escalations). Five events drop under the 10-day cluster rule or because they add no new policy: R01, R04, R06, NK03 and I04. I08 stays in, flagged for a possible confound with the Soleimani strike.

## Data-quality caveats

Privacy-coin liquidity fell after exchange delistings (Binance dropped XMR on 20 Feb 2024) and the EU's MiCA regime took effect in Dec 2024, so events from 2024 on rely on thinner markets. See the "Data Quality Notes" sheet and the split-sample robustness test in `src/robustness.py`.

If you use this dataset, please cite: Pellegrino, D. (2026). *Sanctions and privacy-focused cryptocurrency markets*. M1 thesis, Université Paris 1 Panthéon-Sorbonne.

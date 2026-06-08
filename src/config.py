"""
Configuration: all paths, parameters, and asset definitions.
Edit DATA_FOLDER and EVENTS_FILE to match your local setup.
"""
import os

PROJECT_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER   = os.path.join(PROJECT_ROOT, "data")
EVENTS_FILE   = os.path.join(PROJECT_ROOT, "data", "sanctions_events.xlsx")
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ASSETS    = ['monero', 'zcash', 'dash', 'bitcoin', 'ethereum']
LABELS    = ['XMR',    'ZEC',   'DASH', 'BTC',     'ETH']
TREATMENT = ['XMR', 'ZEC', 'DASH']
CONTROL   = ['BTC', 'ETH']
BENCHMARK = 'bitcoin'

ESTIMATION_WINDOW = (-200, -20)
EVENT_WINDOWS     = [(-1, 1), (-5, 5), (-5, 30)]
MIN_EST_OBS       = 60

DID_WINDOW_DAYS = 180

MONERO_DELISTING_DATE = "2024-02-20"

from pathlib import Path


# ==========================================
# Project paths
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw"

RAW_DATA_FILE = RAW_DATA_DIR / "tweets.csv"


# ==========================================
# X configuration
# ==========================================

X_BASE_URL = "https://x.com"

X_USERNAME = "maradiaga"

MAX_TWEETS = 20


# ==========================================
# Browser configuration
# ==========================================

HEADLESS = False

SLOW_MO = 100
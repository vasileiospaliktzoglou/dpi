APP_TITLE = "PALI Execute"
APP_VERSION = "8.1 tested decision engine"

# Primary Yahoo tickers. Confirm final orders in IBKR because Yahoo EU ETF data may be delayed.
TICKERS = {
    "V60A": "V60A.DE",
    "VNGA80": "VNGA80.MI",
    "VWCE": "VWCE.DE",
}

# Alternative Yahoo tickers if a venue is unavailable.
TICKER_ALIASES = {
    "V60A.DE": ["V60A.DE", "V60A.DU", "V60A.MI"],
    "VNGA80.MI": ["VNGA80.MI", "VNGA80.DE"],
    "VWCE.DE": ["VWCE.DE", "VWCE.MI"],
}

# Offline fallback prices. Used only if Yahoo is temporarily unavailable.
# This prevents Streamlit Cloud from crashing and lets the UI load.
FALLBACK_PRICES = {
    "V60A.DE": 36.72,
    "V60A.DU": 36.72,
    "V60A.MI": 36.72,
    "VNGA80.MI": 43.39,
    "VNGA80.DE": 43.39,
    "VWCE.DE": 163.70,
    "VWCE.MI": 163.70,
}

BASE_AMOUNTS = {
    "V60A": 20000,
    "VNGA80": 10000,
    "VWCE": 0,
}

BENCHMARKS = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DAX": "^GDAXI",
    "VIX": "^VIX",
    "EURUSD": "EURUSD=X",
    "USD Index": "DX-Y.NYB",
    "US 10Y": "^TNX",
    "Gold": "GC=F",
    "Brent Oil": "BZ=F",
    "BTC": "BTC-USD",
}

RISK_BANDS = {
    "normal": 0.50,
    "good": 0.75,
    "strong": 0.90,
    "exceptional": 0.95,
}

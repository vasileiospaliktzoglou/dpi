TICKERS = {
    "V60A": "V60A.DE",
    "VNGA80": "VNGA80.MI",
    "VWCE": "VWCE.DE",
}

ETF_META = {
    "V60A": {
        "name": "Vanguard LifeStrategy 60",
        "role": "Core balanced allocation",
        "amount": 20000,
        "primary_window": "10:00–12:00 CET",
        "bahrain_window": "12:00–14:00 Bahrain",
    },
    "VNGA80": {
        "name": "Vanguard LifeStrategy 80",
        "role": "Core growth allocation",
        "amount": 10000,
        "primary_window": "After US open",
        "bahrain_window": "16:30–18:00 Bahrain",
    },
    "VWCE": {
        "name": "Vanguard FTSE All-World",
        "role": "Global equity allocation",
        "amount": 10000,
        "primary_window": "US overlap",
        "bahrain_window": "16:30–18:30 Bahrain",
    },
}

BENCHMARKS = {
    "S&P": "^GSPC",
    "NASDAQ": "^IXIC",
    "DAX": "^GDAXI",
    "VIX": "^VIX",
    "EURUSD": "EURUSD=X",
    "US10Y": "^TNX",
}

APP_TITLE = "EXECUTE"
APP_VERSION = "6.10.8-simplified-pro"
DEFAULT_ETF = "V60A"
ORDER_SIZE_EUR = 20000

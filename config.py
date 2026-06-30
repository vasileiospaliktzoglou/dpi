APP_TITLE = "PALI EXECUTE"
APP_VERSION = "v7.2"

ETFS = {
    "V60A": {
        "name": "Vanguard LifeStrategy 60% Equity UCITS ETF",
        "ticker": "V60A.DE",
        "role": "Core balanced ETF",
        "risk": "Medium",
        "default_target_offset_atr": 0.80,
        "planned_amount_eur": 20000,
    },
    "VNGA80": {
        "name": "Vanguard LifeStrategy 80% Equity UCITS ETF",
        "ticker": "VNGA80.MI",
        "role": "Growth core ETF",
        "risk": "Medium-high",
        "default_target_offset_atr": 1.00,
        "planned_amount_eur": 10000,
    },
    "VWCE": {
        "name": "Vanguard FTSE All-World UCITS ETF",
        "ticker": "VWCE.DE",
        "role": "Global equity ETF",
        "risk": "High",
        "default_target_offset_atr": 1.10,
        "planned_amount_eur": 10000,
    },
}

MARKET_TICKERS = {
    "Global stocks": "URTH",
    "S&P 500": "SPY",
    "Europe stocks": "VGK",
    "US bonds": "IEF",
    "Volatility": "^VIX",
    "EUR/USD": "EURUSD=X",
}

DATA_DIR = "data"
MEMORY_FILE = "data/PALI_EXECUTE_MEMORY.xlsx"
LOG_DIR = "logs"
LOG_FILE = "logs/app.log"

TICKERS = {
    "V60A": "V60A.DE",
    "VNGA80": "VNGA80.MI",
    "VWCE": "VWCE.DE",
}

BENCHMARKS = {
    "S&P": "^GSPC",
    "NASDAQ": "^IXIC",
    "DAX": "^GDAXI",
    "VIX": "^VIX",
    "EURUSD": "EURUSD=X",
    "DXY": "DX-Y.NYB",
    "US10Y": "^TNX",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Brent": "BZ=F",
    "BTC": "BTC-USD",
}

APP_TITLE = "PALI Execute"
APP_VERSION = "7.0"

DEFAULT_ETF = "V60A"
DEFAULT_PAGE = "Dashboard"
DEFAULT_LAYOUT = "Desktop"

TIMEFRAME_MAP = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "15m"),
    "1M": ("1mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
}

ORDER_SIZE_EUR = 20000

COLORS = {
    "green": "#10b981",
    "red": "#ef4444",
    "blue": "#2563eb",
    "dark": "#111827",
    "muted": "#6b7280",
    "border": "#e5e7eb",
}


MARKET_EXPLAINERS = {
    "S&P": "Broad US risk appetite. Strong moves here influence global ETFs.",
    "NASDAQ": "Growth and technology sentiment. Useful for checking AI/tech risk appetite.",
    "DAX": "European market tone. Relevant because V60A.DE and VWCE.DE trade in Europe.",
    "VIX": "Expected US equity volatility. Below 20 usually supports normal execution; above 25 means caution.",
    "EURUSD": "Currency backdrop for EUR-based investors and USD-heavy global equity funds.",
    "DXY": "US dollar strength. A stronger USD can affect EUR/USD conversion and global assets.",
    "US10Y": "Long-term rate pressure. Higher yields can weigh on equity valuations.",
    "Gold": "Safe-haven demand. Rising gold can signal caution or geopolitical stress.",
    "Silver": "Cyclical + precious metal signal. More volatile than gold.",
    "Brent": "Oil inflation and geopolitical risk gauge. A spike can pressure rates and equities.",
    "BTC": "Speculative liquidity proxy. Useful but not central to ETF execution.",
}

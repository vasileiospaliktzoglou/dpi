def css() -> str:
    return """
    <style>
    :root {
      --bg:#06080d; --panel:#0d1422; --text:#f8fafc; --muted:#9aa6b5;
      --line:rgba(148,163,184,.20); --good:#22c55e; --bad:#ef4444; --blue:#60a5fa;
    }
    header[data-testid="stHeader"] { display:none !important; height:0 !important; }
    div[data-testid="stToolbar"], div[data-testid="stDecoration"], #MainMenu, footer { display:none !important; visibility:hidden !important; height:0 !important; }
    .stApp { background:linear-gradient(180deg,#05070c 0%,#07111f 48%,#05070c 100%); color:var(--text); }
    .block-container { padding-top:.75rem; padding-bottom:2.5rem; max-width:1120px; }
    h1 { font-size:2.35rem !important; font-weight:950 !important; letter-spacing:-.065em !important; margin-bottom:0 !important; }
    h2, h3 { letter-spacing:-.025em !important; }
    [data-testid="stMetric"] {
      background:rgba(13,20,34,.92); border:1px solid var(--line); border-radius:20px;
      padding:14px 16px; box-shadow:0 14px 40px rgba(0,0,0,.20);
    }
    [data-testid="stMetricLabel"] { color:#cbd5e1 !important; }
    [data-testid="stMetricValue"] { font-weight:900 !important; letter-spacing:-.045em !important; }
    [data-testid="stMetricDelta"] { font-weight:800 !important; }
    div[data-testid="stDataFrame"] { border-radius:18px; overflow:hidden; }
    div[data-testid="stTabs"] button { font-weight:800; border-radius:999px; }
    div[role="radiogroup"] { gap:8px; flex-wrap:wrap; }
    div[role="radiogroup"] label {
      background:rgba(13,20,34,.88); border:1px solid var(--line); border-radius:999px;
      padding:8px 13px; margin-right:6px;
    }
    .stAlert { border-radius:18px !important; }
    section[data-testid="stSidebar"] { display:none; }
    @media (max-width: 720px) {
      .block-container { padding-left:.65rem; padding-right:.65rem; padding-top:.45rem; }
      h1 { font-size:1.85rem !important; }
      h2 { font-size:1.25rem !important; }
      [data-testid="stMetric"] { padding:12px 13px; border-radius:16px; }
      [data-testid="stMetricValue"] { font-size:1.35rem !important; }
      div[data-testid="column"] { min-width:100% !important; }
      div[data-testid="stHorizontalBlock"] { gap:.55rem; }
    }
    </style>
    """

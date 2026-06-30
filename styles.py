def css() -> str:
    return """
    <style>
    :root {
      --bg:#070a10; --surface:#0f172a; --surface2:#111827; --surface3:#0b1220;
      --text:#eef2ff; --muted:#94a3b8; --faint:#64748b; --line:#1e293b;
      --good:#22c55e; --warn:#f59e0b; --bad:#ef4444; --blue:#60a5fa; --cyan:#22d3ee;
    }
    header[data-testid="stHeader"] { display:none !important; }
    div[data-testid="stToolbar"] { visibility:hidden !important; height:0 !important; position:fixed; }
    div[data-testid="stDecoration"] { display:none !important; }
    #MainMenu { visibility:hidden; }
    footer { visibility:hidden; }
    .stApp { background: radial-gradient(circle at top left, #132033 0, var(--bg) 36%, #04060a 100%); color: var(--text); }
    [data-testid="stSidebar"] { background: #060913; border-right: 1px solid var(--line); }
    .block-container { padding-top: .85rem; padding-bottom: 2rem; max-width: 1180px; }

    .app-shell { width:100%; }
    .topbar { display:flex; justify-content:space-between; align-items:center; gap:16px; padding:4px 0 18px; }
    .brand { font-size:28px; font-weight:900; letter-spacing:-.045em; }
    .subtitle { color:var(--muted); font-size:13px; margin-top:2px; }
    .version { color:#cbd5e1; background:rgba(15,23,42,.78); border:1px solid var(--line); padding:8px 12px; border-radius:999px; font-size:12px; white-space:nowrap; }

    .hero { background: linear-gradient(135deg, rgba(96,165,250,.16), rgba(34,197,94,.08)); border:1px solid #263653; border-radius:28px; padding:26px; margin:4px 0 18px; box-shadow:0 22px 60px rgba(0,0,0,.26); }
    .hero-grid { display:grid; grid-template-columns: 1.15fr .85fr; gap:20px; align-items:end; }
    .eyebrow { color:#93c5fd; text-transform:uppercase; letter-spacing:.13em; font-size:11px; font-weight:800; margin-bottom:6px; }
    .decision { font-size:46px; line-height:1; font-weight:950; letter-spacing:-.055em; margin:2px 0 10px; }
    .plain { color:#dbeafe; font-size:16px; line-height:1.55; margin:0; }
    .muted { color:var(--muted); font-size:13px; line-height:1.45; }
    .tiny { color:var(--faint); font-size:12px; }
    .hero-metrics { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    .mini { background:rgba(5,9,18,.38); border:1px solid rgba(148,163,184,.14); border-radius:18px; padding:12px; }
    .mini-value { font-size:20px; font-weight:850; letter-spacing:-.03em; }
    .mini-label { color:var(--muted); font-size:12px; margin-top:2px; }

    .section-title { margin:24px 0 10px; font-size:18px; font-weight:850; letter-spacing:-.02em; }
    .grid2 { display:grid; grid-template-columns:1.25fr .75fr; gap:14px; margin:14px 0; }
    .cards { display:grid; grid-template-columns: repeat(3, 1fr); gap:14px; margin:12px 0; }
    .card { background: rgba(15,23,42,.92); border:1px solid var(--line); border-radius:22px; padding:18px; box-shadow: 0 16px 42px rgba(0,0,0,.18); }
    .card h3 { margin:0 0 8px 0; font-size:19px; letter-spacing:-.02em; }
    .metric { font-size:28px; font-weight:900; letter-spacing:-.04em; margin-top:4px; }
    .status { display:inline-flex; align-items:center; gap:8px; border-radius:999px; padding:7px 10px; border:1px solid var(--line); background:#0b1220; color:#cbd5e1; font-size:13px; margin:4px 6px 0 0; }
    .listrow { display:flex; justify-content:space-between; border-bottom:1px solid var(--line); padding:10px 0; gap:12px; }
    .listrow:last-child { border-bottom:none; }
    .divider { height:1px; background:var(--line); margin:14px 0; }
    .action-row { display:grid; grid-template-columns: 1fr auto; gap:12px; align-items:center; }
    .soft { background: rgba(15,23,42,.60); border:1px solid rgba(148,163,184,.14); border-radius:18px; padding:14px; }

    div[data-testid="stSegmentedControl"] label { font-weight:800; }
    div[data-baseweb="tab-list"] { gap: 6px; }
    button[data-baseweb="tab"] { background:#0b1220; border-radius:999px; border:1px solid var(--line); padding:8px 14px; }

    @media (max-width: 820px) {
      .block-container { padding-left:.75rem; padding-right:.75rem; padding-top:.55rem; }
      .topbar { display:block; padding-bottom:12px; }
      .version { display:inline-block; margin-top:10px; }
      .hero { border-radius:22px; padding:18px; }
      .hero-grid, .grid2, .cards { grid-template-columns:1fr; }
      .decision { font-size:34px; }
      .hero-metrics { grid-template-columns:1fr; }
      .card { border-radius:18px; padding:15px; }
      .metric { font-size:24px; }
    }
    </style>
    """

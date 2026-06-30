def css() -> str:
    return """
    <style>
    :root {
      --bg:#06080d; --panel:#0d1422; --panel2:#101827; --panel3:#111c2f;
      --text:#f8fafc; --muted:#9aa6b5; --soft:#cbd5e1; --line:rgba(148,163,184,.18);
      --good:#22c55e; --warn:#f59e0b; --bad:#ef4444; --blue:#60a5fa;
    }
    header[data-testid="stHeader"] { display:none !important; height:0 !important; }
    div[data-testid="stToolbar"], div[data-testid="stDecoration"], #MainMenu, footer { display:none !important; visibility:hidden !important; height:0 !important; }
    .stApp { background:linear-gradient(180deg,#05070c 0%,#07111f 46%,#05070c 100%); color:var(--text); }
    [data-testid="stSidebar"] { background:#070a12; border-right:1px solid var(--line); }
    .block-container { padding-top:.55rem; padding-bottom:2rem; max-width:1180px; }
    .brandbar { display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:14px; }
    .brand { font-size:30px; font-weight:950; letter-spacing:-.06em; }
    .sub { color:var(--muted); font-size:13px; }
    .stamp { color:var(--muted); font-size:12px; text-align:right; }

    .hero { border-radius:30px; padding:24px; background:linear-gradient(135deg,rgba(96,165,250,.20),rgba(34,197,94,.09)); border:1px solid rgba(96,165,250,.25); box-shadow:0 24px 70px rgba(0,0,0,.35); }
    .hero-grid { display:grid; grid-template-columns:1.1fr .9fr; gap:20px; align-items:end; }
    .eyebrow { color:#93c5fd; text-transform:uppercase; letter-spacing:.14em; font-size:11px; font-weight:850; margin-bottom:6px; }
    .decision { font-size:48px; line-height:.96; font-weight:950; letter-spacing:-.065em; margin:2px 0 12px; }
    .plain { color:#e5efff; font-size:15.5px; line-height:1.55; margin:0; }
    .muted { color:var(--muted); font-size:13px; line-height:1.45; }
    .small { color:var(--muted); font-size:12px; }
    .hero-metrics { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    .mini { background:rgba(5,9,18,.48); border:1px solid var(--line); border-radius:18px; padding:13px; }
    .mini-value { font-size:21px; font-weight:900; letter-spacing:-.035em; }
    .mini-label { color:var(--muted); font-size:12px; margin-top:3px; }

    .section-title { margin:24px 0 10px; font-size:18px; font-weight:900; letter-spacing:-.025em; }
    .grid2 { display:grid; grid-template-columns:1.15fr .85fr; gap:14px; margin:14px 0; }
    .cards { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:14px; margin:12px 0; }
    .card { background:rgba(13,20,34,.94); border:1px solid var(--line); border-radius:22px; padding:18px; box-shadow:0 18px 42px rgba(0,0,0,.20); overflow:hidden; }
    .card h3 { margin:0; font-size:19px; letter-spacing:-.025em; }
    .metric { font-size:28px; font-weight:950; letter-spacing:-.045em; }
    .row { display:flex; align-items:center; justify-content:space-between; gap:14px; }
    .divider { height:1px; background:var(--line); margin:14px 0; }
    .pill { display:inline-flex; align-items:center; border-radius:999px; padding:7px 10px; background:rgba(148,163,184,.08); border:1px solid var(--line); color:#dbeafe; font-size:12px; margin:3px 4px 0 0; }
    .market-row { display:grid; grid-template-columns:1fr auto auto; gap:12px; align-items:center; padding:10px 0; border-bottom:1px solid var(--line); }
    .market-row:last-child { border-bottom:none; }
    .positive { color:var(--good); font-weight:800; }
    .negative { color:var(--bad); font-weight:800; }
    .soft { background:rgba(13,20,34,.62); border:1px solid var(--line); border-radius:18px; padding:15px; }

    div[data-testid="stRadio"] label { font-weight:700; }
    div[role="radiogroup"] { gap:8px; }
    div[role="radiogroup"] label { background:rgba(13,20,34,.88); border:1px solid var(--line); border-radius:999px; padding:8px 12px; margin-right:6px; }
    button[kind="secondary"] { border-radius:999px !important; border:1px solid var(--line) !important; background:rgba(13,20,34,.9) !important; }

    @media (max-width: 840px) {
      .block-container { padding-left:.72rem; padding-right:.72rem; padding-top:.45rem; }
      .brandbar { display:block; margin-bottom:10px; }
      .brand { font-size:27px; }
      .stamp { text-align:left; margin-top:4px; }
      .hero { border-radius:22px; padding:18px; }
      .hero-grid, .grid2, .cards { grid-template-columns:1fr; }
      .decision { font-size:36px; }
      .hero-metrics { grid-template-columns:1fr 1fr; }
      .mini { padding:11px; }
      .mini-value { font-size:18px; }
      .card { border-radius:18px; padding:15px; }
      .metric { font-size:24px; }
      .market-row { grid-template-columns:1fr auto; }
      .market-row .small { grid-column:1 / -1; }
    }
    @media (max-width: 430px) {
      .hero-metrics { grid-template-columns:1fr; }
      .decision { font-size:32px; }
      .brand { font-size:25px; }
    }
    </style>
    """

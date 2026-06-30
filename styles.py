def css() -> str:
    return """
    <style>
    :root { --bg:#080b12; --panel:#111827; --panel2:#0f172a; --muted:#94a3b8; --text:#e5e7eb; --line:#1f2937; --good:#22c55e; --warn:#f59e0b; --bad:#ef4444; --accent:#60a5fa; }
    .stApp { background: radial-gradient(circle at top left, #111827 0, #080b12 34%, #06070b 100%); color: var(--text); }
    [data-testid="stSidebar"] { background: #070a10; border-right: 1px solid var(--line); }
    .block-container { padding-top: 1.2rem; max-width: 1180px; }
    .top { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:16px; }
    .brand { font-size:26px; font-weight:800; letter-spacing:-.03em; }
    .sub { color:var(--muted); font-size:14px; margin-top:4px; }
    .version { color:#cbd5e1; background:#0f172a; border:1px solid var(--line); padding:8px 12px; border-radius:999px; font-size:12px; white-space:nowrap; }
    .hero { background: linear-gradient(135deg, rgba(96,165,250,.14), rgba(34,197,94,.07)); border:1px solid #23324a; border-radius:24px; padding:24px; margin:14px 0 18px 0; }
    .eyebrow { color:#93c5fd; text-transform:uppercase; letter-spacing:.12em; font-size:12px; font-weight:700; }
    .decision { font-size:42px; line-height:1.05; font-weight:900; letter-spacing:-.04em; margin:8px 0; }
    .plain { color:#cbd5e1; font-size:16px; line-height:1.55; max-width:860px; }
    .cards { display:grid; grid-template-columns: repeat(3, 1fr); gap:14px; margin:12px 0; }
    .card { background: rgba(15,23,42,.92); border:1px solid var(--line); border-radius:20px; padding:18px; box-shadow: 0 16px 40px rgba(0,0,0,.16); }
    .card h3 { margin:0 0 8px 0; font-size:18px; }
    .metric { font-size:28px; font-weight:800; letter-spacing:-.03em; margin-top:6px; }
    .muted { color:var(--muted); font-size:13px; line-height:1.45; }
    .grid2 { display:grid; grid-template-columns:1.4fr .9fr; gap:14px; margin:14px 0; }
    .listrow { display:flex; justify-content:space-between; border-bottom:1px solid var(--line); padding:10px 0; gap:12px; }
    .listrow:last-child { border-bottom:none; }
    .pill { display:inline-flex; align-items:center; gap:8px; border-radius:999px; padding:7px 10px; border:1px solid var(--line); background:#0b1220; color:#cbd5e1; font-size:13px; margin-right:6px; }
    .good { color: var(--good); } .warn { color: var(--warn); } .bad { color: var(--bad); }
    .seg-note { color:var(--muted); font-size:13px; margin-top:-6px; margin-bottom:8px; }
    div[data-testid="stSegmentedControl"] { background: transparent; }
    @media (max-width: 760px) {
      .top { display:block; }
      .version { display:inline-block; margin-top:10px; }
      .decision { font-size:32px; }
      .cards, .grid2 { grid-template-columns:1fr; }
      .card, .hero { border-radius:18px; padding:16px; }
      .block-container { padding-left: .75rem; padding-right: .75rem; }
    }
    </style>
    """

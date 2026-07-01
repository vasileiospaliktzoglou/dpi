def css() -> str:
    return """
    <style>
    :root {
      --bg:#0D1424;
      --bg2:#121C30;
      --panel:#162238;
      --panel2:#1A2740;
      --panel3:#22304A;
      --text:#EAF1FA;
      --text2:#D7E0EE;
      --muted:#9FB0C7;
      --line:rgba(159,176,199,.20);
      --good:#3DDC84;
      --warn:#F4B740;
      --bad:#F87171;
      --blue:#7CB7FF;
      --purple:#B59CFF;
    }

    header[data-testid="stHeader"] { display:none !important; height:0 !important; }
    div[data-testid="stToolbar"], div[data-testid="stDecoration"], #MainMenu, footer {
      display:none !important; visibility:hidden !important; height:0 !important;
    }
    .stApp {
      background:
        radial-gradient(circle at top left, rgba(124,183,255,.16), transparent 34%),
        linear-gradient(180deg,var(--bg) 0%,#0D1526 48%,#0A1120 100%);
      color:var(--text);
    }
    [data-testid="stSidebar"] { display:none !important; }
    .block-container { padding-top:.55rem; padding-bottom:2.2rem; max-width:1180px; }
    * { box-sizing:border-box; }
    .card, .timing-card, .market-card, .soft, .mini { overflow-wrap:break-word; word-break:normal; }

    .brandbar {
      display:flex; align-items:center; justify-content:space-between; gap:14px;
      margin-bottom:14px; padding:2px 0 4px;
    }
    .brand { font-size:30px; font-weight:950; letter-spacing:-.06em; color:var(--text); }
    .sub { color:var(--muted); font-size:13px; max-width:650px; }
    .stamp { color:var(--muted); font-size:12px; text-align:right; white-space:normal; }
    .live-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--good); margin-right:6px; box-shadow:0 0 0 5px rgba(61,220,132,.10); }

    .hero {
      border-radius:30px; padding:24px;
      background:linear-gradient(135deg,rgba(124,183,255,.20),rgba(61,220,132,.08));
      border:1px solid rgba(124,183,255,.25);
      box-shadow:0 24px 70px rgba(4,8,18,.34);
    }
    .hero-grid { display:grid; grid-template-columns:minmax(0,1.08fr) minmax(280px,.92fr); gap:20px; align-items:end; }
    .eyebrow { color:#A6CCFF; text-transform:uppercase; letter-spacing:.14em; font-size:11px; font-weight:850; margin-bottom:6px; }
    .decision { font-size:clamp(34px,5.4vw,48px); line-height:.98; font-weight:950; letter-spacing:-.065em; margin:2px 0 12px; color:var(--text); }
    .plain { color:var(--text2); font-size:15.5px; line-height:1.55; margin:0; }
    .muted { color:var(--muted); font-size:13px; line-height:1.45; min-width:0; }
    .small { color:var(--muted); font-size:12px; }
    .hero-metrics { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
    .mini { background:rgba(17,26,46,.62); border:1px solid var(--line); border-radius:18px; padding:13px; min-width:0; }
    .mini-value { font-size:clamp(17px,2.5vw,21px); font-weight:900; letter-spacing:-.035em; color:var(--text); }
    .mini-label { color:var(--muted); font-size:12px; margin-top:3px; }

    .section-title { margin:24px 0 10px; font-size:18px; font-weight:900; letter-spacing:-.025em; color:var(--text); }
    .first-section { margin-top:8px; }

    .market-grid { display:grid; grid-template-columns:repeat(3,minmax(180px,1fr)); gap:12px; margin:12px 0; }
    .market-card {
      background:linear-gradient(180deg,rgba(26,39,64,.98),rgba(21,32,51,.94));
      border:1px solid var(--line); border-radius:20px; padding:15px; min-width:0;
      box-shadow:0 14px 34px rgba(4,8,18,.16); overflow:hidden;
    }
    .market-top { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; min-width:0; }
    .market-name { font-weight:850; font-size:14px; line-height:1.15; color:var(--text); overflow-wrap:normal; word-break:normal; }
    .ticker { color:var(--muted); font-size:11px; margin-top:3px; letter-spacing:.06em; white-space:nowrap; }
    .market-price { font-size:clamp(20px,3vw,27px); font-weight:950; letter-spacing:-.04em; margin-top:10px; white-space:nowrap; color:var(--text); }
    .market-move { font-size:13px; font-weight:900; white-space:nowrap; padding:4px 8px; border-radius:999px; background:rgba(159,176,199,.10); }
    .market-sub { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:11px; }
    .market-sub div { background:rgba(159,176,199,.08); border-radius:12px; padding:7px 8px; min-width:0; }
    .market-sub span { display:block; font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; white-space:nowrap; }
    .market-sub b { font-size:12px; white-space:nowrap; }
    .status { display:inline-flex; align-items:center; border-radius:999px; padding:5px 9px; font-size:11px; font-weight:950; letter-spacing:.08em; text-transform:uppercase; white-space:normal; max-width:100%; line-height:1.15; }
    .status-wait { color:var(--warn); background:rgba(244,183,64,.16); border:1px solid rgba(244,183,64,.30); }
    .status-ready { color:var(--good); background:rgba(61,220,132,.14); border:1px solid rgba(61,220,132,.30); }
    .status-monitor { color:var(--muted); background:rgba(159,176,199,.10); border:1px solid var(--line); }
    .cards, .timing-cards { display:grid; grid-template-columns:repeat(3, minmax(245px,1fr)); gap:14px; margin:12px 0; }
    .card, .timing-card {
      background:rgba(21,32,51,.94); border:1px solid var(--line); border-radius:22px; padding:18px;
      box-shadow:0 18px 42px rgba(4,8,18,.20); overflow:hidden; min-width:0;
    }
    .timing-card { background:linear-gradient(180deg,rgba(26,39,64,.98),rgba(21,32,51,.94)); }
    .timing-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
    .timing-score { font-size:28px; font-weight:950; color:var(--good); white-space:nowrap; letter-spacing:-.04em; }
    .timing-grid { display:grid; grid-template-columns:1fr; gap:8px; margin-top:14px; }
    .timing-grid div { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:9px 10px; border-radius:14px; background:rgba(159,176,199,.08); }
    .timing-grid span { color:var(--muted); font-size:12px; }
    .timing-grid b { color:var(--text); font-size:13px; text-align:right; }
    .card h3 { margin:0; font-size:clamp(16px,1.8vw,19px); letter-spacing:-.025em; color:var(--text); line-height:1.18; }
    .metric { font-size:clamp(22px,3.2vw,28px); font-weight:950; letter-spacing:-.045em; color:var(--text); white-space:nowrap; }
    .row { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; min-width:0; }
    .row > * { min-width:0; }
    .divider { height:1px; background:var(--line); margin:14px 0; }
    .pill {
      display:inline-flex; align-items:center; max-width:100%; border-radius:999px; padding:7px 10px;
      background:rgba(159,176,199,.10); border:1px solid var(--line); color:#DDEBFF; font-size:12px; margin:3px 4px 0 0;
    }
    .market-row {
      display:grid; grid-template-columns:minmax(0,1fr) minmax(74px,auto) minmax(72px,auto);
      gap:12px; align-items:center; padding:10px 0; border-bottom:1px solid var(--line);
    }
    .market-row:last-child { border-bottom:none; }
    .positive { color:var(--good); font-weight:800; white-space:nowrap; }
    .negative { color:var(--bad); font-weight:800; white-space:nowrap; }
    .soft { background:rgba(21,32,51,.64); border:1px solid var(--line); border-radius:18px; padding:15px; }
    .stat-line { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:7px 0; }
    .stat-label { color:var(--muted); font-size:13px; }
    .stat-value { color:var(--text); font-weight:850; text-align:right; }

    div[data-testid="stRadio"] label { font-weight:700; color:var(--text2); }
    div[role="radiogroup"] { gap:8px; flex-wrap:wrap; }
    div[role="radiogroup"] label {
      background:rgba(21,32,51,.88); border:1px solid var(--line); border-radius:999px;
      padding:8px 12px; margin-right:6px; color:var(--text2);
    }
    button[kind="secondary"], .stButton > button { border-radius:16px !important; border:1px solid var(--line) !important; background:rgba(21,32,51,.94) !important; color:var(--text) !important; min-height:46px; font-weight:850 !important; white-space:normal !important; }
    .stButton > button:hover { border-color:rgba(124,183,255,.55) !important; background:rgba(26,39,64,.98) !important; }

    @media (max-width: 920px) {
      .cards, .timing-cards, .market-grid { grid-template-columns:1fr 1fr; }
      .hero-grid { grid-template-columns:1fr; }
    }
    @media (max-width: 640px) {
      .block-container { padding-left:.72rem; padding-right:.72rem; padding-top:.45rem; }
      .market-grid { grid-template-columns:1fr; }
      .brandbar { display:block; margin-bottom:10px; }
      .brand { font-size:27px; }
      .stamp { text-align:left; margin-top:4px; }
      .hero { border-radius:22px; padding:18px; }
      .decision { font-size:34px; }
      .hero-metrics { grid-template-columns:1fr 1fr; }
      .mini { padding:11px; }
      .card { border-radius:18px; padding:15px; }
      .metric { font-size:23px; }
      .market-row { grid-template-columns:minmax(0,1fr) auto; }
      .market-row > div:nth-child(3) { grid-column:2; }
      .section-title { margin-top:20px; }
    }
    @media (max-width: 430px) {
      .hero-metrics { grid-template-columns:1fr; }
      .decision { font-size:31px; }
      .brand { font-size:25px; }
      .row { gap:8px; }
      .metric { white-space:normal; text-align:right; }
    }
    /* Final responsive compatibility patch: keep the same visual design, but make cards/charts fit phones and tablets. */
    .element-container, .stPlotlyChart, [data-testid="stPlotlyChart"] { max-width:100% !important; overflow:hidden !important; }
    iframe { max-width:100% !important; }
    .js-plotly-plot, .plot-container, .svg-container { width:100% !important; max-width:100% !important; }

    @media (max-width: 920px) {
      .cards, .timing-cards, .market-grid { grid-template-columns:1fr 1fr; }
      .card, .timing-card { min-height:auto; }
    }
    @media (max-width: 760px) {
      .cards, .timing-cards, .market-grid { grid-template-columns:1fr; }
      .stat-line { align-items:flex-start; }
      .stat-label { max-width:62%; }
      .stat-value { max-width:38%; overflow-wrap:normal; word-break:keep-all; }
      .stPlotlyChart { width:100% !important; }
    }
    @media (max-width: 640px) {
      .block-container { padding-left:.72rem !important; padding-right:.72rem !important; }
      .card, .timing-card { width:100%; }
      .row { align-items:flex-start; }
      .row .metric { flex-shrink:1; max-width:46%; overflow-wrap:normal; word-break:keep-all; }
      .card h3 { font-size:16px; }
      .muted { font-size:12.5px; }
      .stat-line { padding:8px 0; }
      div[data-testid="column"] { width:100% !important; flex:1 1 100% !important; }
      div[data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; gap:.65rem !important; }
    }
    @media (max-width: 430px) {
      .card, .timing-card { padding:14px; }
      .row .metric { max-width:46%; font-size:21px; }
      .stat-label { max-width:58%; font-size:12px; }
      .stat-value { max-width:42%; font-size:12.5px; }
      .ticker, .eyebrow { letter-spacing:.10em; }
      .section-title { font-size:17px; }
    }

    
/* Final card wrapping + safe market stat helpers */
.neutral { color: var(--muted); font-weight: 800; white-space: nowrap; }
.market-sub b { display:block; overflow:hidden; text-overflow:ellipsis; max-width:100%; }
.market-card, .card, .timing-card { word-break: normal; overflow-wrap: anywhere; }
@media (max-width: 520px) {
  .market-sub { grid-template-columns: 1fr 1fr; gap: 6px; }
  .market-sub div { min-width: 0; }
  .market-sub span { font-size: 9px; }
  .market-sub b { font-size: 11px; }
}

</style>
    """

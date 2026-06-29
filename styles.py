def load_css():
    return r"""
<style>
:root{
    --navy:#061525;
    --navy2:#0b2137;
    --ink:#0f172a;
    --muted:#64748b;
    --line:#e5e7eb;
    --soft:#f8fafc;
    --blue:#2563eb;
    --green:#059669;
    --red:#dc2626;
    --amber:#d97706;
}
header, .stDeployButton, [data-testid='stToolbar']{display:none!important;}
.block-container{padding:0.55rem 1.05rem 1.2rem 1.05rem!important;max-width:1500px;}
div[data-testid="stVerticalBlock"]{gap:0.55rem!important;}
div[data-testid="stHorizontalBlock"]{gap:0.75rem!important;}
h1,h2,h3{letter-spacing:-.02em;color:var(--ink);} 
h1{font-size:24px!important;margin:0!important;font-weight:900!important;}
h2{font-size:20px!important;margin:0!important;font-weight:850!important;}
h3{font-size:16px!important;margin:0!important;font-weight:800!important;}
[data-testid="stSidebar"]{min-width:285px;max-width:285px;background:linear-gradient(180deg,#071827 0%,#0b1f33 100%);} 
[data-testid="stSidebar"] *{color:#e5eef8!important;}
[data-testid="stSidebar"] .stRadio label{font-size:12px!important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#b8c7d9!important;}
.market-row{display:flex;justify-content:space-between;align-items:center;padding:6px 2px;border-bottom:1px solid rgba(255,255,255,.08);font-size:12px;}
.sidebar-panel{border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.035);border-radius:14px;padding:12px;margin:10px 0;}
.app-topbar{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid var(--line);padding:2px 0 12px 0;margin-bottom:8px;}
.app-title{font-size:24px;font-weight:950;color:var(--ink);line-height:1.05;}
.app-subtitle{font-size:13px;color:var(--muted);margin-top:4px;}
.live-pill{display:inline-flex;align-items:center;gap:7px;border:1px solid #bbf7d0;background:#ecfdf5;color:#047857;border-radius:999px;padding:7px 12px;font-size:12px;font-weight:900;}
.live-dot{width:8px;height:8px;border-radius:999px;background:#10b981;display:inline-block;}
.section-title{font-size:14px;font-weight:950;color:var(--ink);text-transform:uppercase;letter-spacing:.04em;margin:12px 0 6px 0;}
.section-subtitle{font-size:12px;color:var(--muted);margin:-2px 0 8px 0;}
.kpi-card{border:1px solid var(--line);border-radius:16px;background:#fff;padding:16px;min-height:120px;box-shadow:0 8px 22px rgba(15,23,42,.045);}
.kpi-label{font-size:11px;text-transform:uppercase;letter-spacing:.05em;font-weight:950;color:#64748b;}
.kpi-main{font-size:30px;font-weight:950;line-height:1.05;margin-top:8px;color:#0f172a;}
.kpi-main.green{color:#059669;}.kpi-main.blue{color:#2563eb;}.kpi-main.amber{color:#d97706;}.kpi-main.red{color:#dc2626;}
.kpi-note{font-size:12px;color:#64748b;margin-top:8px;line-height:1.45;}
.chart-stage{border:1px solid var(--line);border-radius:18px;background:#fff;padding:18px;box-shadow:0 10px 28px rgba(15,23,42,.055);margin:10px 0 16px 0;}
.chart-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;}
.chart-title{font-size:18px;font-weight:950;color:var(--ink);}
.chart-caption{font-size:12px;color:var(--muted);margin-top:3px;}
.command-card{border:1px solid #dbeafe;border-radius:18px;background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);padding:20px;box-shadow:0 10px 26px rgba(15,23,42,.05);}
.command-grid{display:grid;grid-template-columns:1.05fr 1fr;gap:18px;align-items:stretch;}
.command-left{border-right:1px solid var(--line);padding-right:18px;}
.command-label{font-size:11px;text-transform:uppercase;font-weight:950;color:#64748b;letter-spacing:.05em;}
.command-action{display:inline-flex;border:1px solid #a7f3d0;background:#ecfdf5;color:#047857;border-radius:999px;padding:5px 10px;font-size:11px;font-weight:950;margin:7px 0 8px 0;}
.command-price{font-size:44px;font-weight:950;color:#059669;line-height:1;margin:6px 0;letter-spacing:-.04em;}
.command-text{font-size:13px;color:#334155;line-height:1.55;max-width:620px;}
.mini-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff;}
.mini-cell{padding:13px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);min-height:78px;}
.mini-cell:nth-child(3n){border-right:none;}
.mini-cell:nth-last-child(-n+3){border-bottom:none;}
.mini-label{font-size:10px;text-transform:uppercase;letter-spacing:.05em;font-weight:900;color:#64748b;}
.mini-value{font-size:18px;font-weight:950;color:#0f172a;margin-top:5px;}
.code-strip{background:#f8fafc;border:1px solid var(--line);border-radius:12px;padding:10px 12px;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace;font-size:13px;margin-top:12px;color:#0f172a;}
.card{border:1px solid var(--line);border-radius:16px;background:#fff;padding:16px;box-shadow:0 4px 18px rgba(15,23,42,.035);}
.card-title{font-size:13px;font-weight:950;color:var(--ink);text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px;}
.card-big{font-size:32px;font-weight:950;line-height:1.05;color:var(--ink);}
.card-text{font-size:13px;color:#334155;line-height:1.55;margin-top:8px;}
.status-card-blue{border-color:#bfdbfe;background:#eff6ff;}.status-card-green{border-color:#bbf7d0;background:#ecfdf5;}.status-card-amber{border-color:#fde68a;background:#fffbeb;}.status-card-red{border-color:#fecaca;background:#fef2f2;}
.progress-bg{width:100%;height:10px;background:#e5e7eb;border-radius:999px;overflow:hidden;margin:10px 0;}
.progress-fill{height:10px;border-radius:999px;background:#2563eb;}
.progress-fill-good{height:10px;border-radius:999px;background:#059669;}
.progress-fill-warn{height:10px;border-radius:999px;background:#d97706;}
.factor-card,.insight-card,.dip-score,.deployment-card,.regime-card,.live-card,.priority-card,.style-card,.playbook-step,.journal-card,.lesson-card{border:1px solid var(--line);border-radius:16px;background:#fff;padding:16px;box-shadow:0 4px 18px rgba(15,23,42,.035);}
.factor-head,.insight-title,.style-title,.step-title{font-size:14px;font-weight:950;color:var(--ink);margin-bottom:6px;}
.factor-body,.insight-text,.step-body,.meaning-text{font-size:13px;line-height:1.55;color:#334155;}
.dip-label,.hero-title{font-size:11px;text-transform:uppercase;color:#64748b;font-weight:950;letter-spacing:.05em;}
.dip-score-big,.regime-big,.deployment-big,.priority-score,.live-big{font-size:32px;font-weight:950;line-height:1.05;color:var(--ink);}
.deployment-card{border-color:#bbf7d0;background:#ecfdf5;}.deployment-big{color:#047857;}.regime-card{border-color:#bfdbfe;background:#eff6ff;}.regime-big{color:#1d4ed8;}
.badge{display:inline-flex;align-items:center;border-radius:999px;padding:5px 10px;font-size:11px;font-weight:950;margin:2px 0 8px 0;}.badge-buy{background:#ecfdf5;color:#047857;border:1px solid #a7f3d0;}.badge-wait{background:#fffbeb;color:#b45309;border:1px solid #fde68a;}.badge-hold{background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;}
.hero-card{border:1px solid #111827;border-radius:18px;padding:20px;background:#111827;color:white;box-shadow:0 10px 28px rgba(15,23,42,.15);}.hero-price{font-size:48px;font-weight:950;color:#10b981;font-family:monospace;line-height:1;margin-top:6px;margin-bottom:10px;}.hero-text{font-size:13px;line-height:1.65;color:#e5e7eb;}
.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;}.kpi-box{border:1px solid rgba(255,255,255,.18);border-radius:10px;padding:8px;background:rgba(255,255,255,.055);}.kpi-box .kpi-value{color:#fff;font-size:16px;}
.sentiment-risk-on{border:1px solid #bbf7d0;background:#ecfdf5;color:#047857;border-radius:16px;padding:16px;}.sentiment-neutral{border:1px solid #e5e7eb;background:#f9fafb;color:#374151;border-radius:16px;padding:16px;}.sentiment-defensive{border:1px solid #fde68a;background:#fffbeb;color:#92400e;border-radius:16px;padding:16px;}.sentiment-risk-off{border:1px solid #fecaca;background:#fef2f2;color:#991b1b;border-radius:16px;padding:16px;}.sentiment-big{font-size:28px;font-weight:950;line-height:1.05;}
.score-scale{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:10px;}.score-scale div{font-size:11px;border:1px solid #e5e7eb;border-radius:8px;padding:7px;background:rgba(255,255,255,.55);text-align:center;color:#334155;}
.chart-story-card,.chart-note-card{border:1px solid #dbeafe;background:#eff6ff;border-radius:14px;padding:12px;margin:8px 0 12px 0;font-size:13px;line-height:1.55;color:#1f2937;}.chart-story-title{font-size:14px;font-weight:950;color:#0f172a;margin-bottom:8px;}.chart-progress-bg{width:100%;height:9px;border-radius:999px;background:#e5e7eb;overflow:hidden;}.chart-progress-fill{height:9px;border-radius:999px;background:#2563eb;}
.section-separator{height:1px;background:#e5e7eb;margin:18px 0;}
.small-muted{font-size:12px;color:#64748b;line-height:1.45;}.meaning-main{font-size:24px;font-weight:950;color:#111827;line-height:1.1;margin-top:4px;}.meaning-title{font-size:11px;text-transform:uppercase;color:#64748b;font-weight:950;letter-spacing:.05em;}
@media (max-width:900px){
    .block-container{padding:0.25rem 0.45rem 0.9rem 0.45rem!important;}
    [data-testid="stSidebar"]{min-width:245px;max-width:245px;}
    .app-topbar{display:block;}
    .live-pill{margin-top:8px;}
    .kpi-card{min-height:auto;padding:13px;}
    .kpi-main{font-size:24px;}
    .chart-stage{padding:10px;border-radius:14px;}
    .command-grid{grid-template-columns:1fr;gap:12px;}
    .command-left{border-right:none;border-bottom:1px solid var(--line);padding-right:0;padding-bottom:12px;}
    .command-price{font-size:36px;}
    .mini-grid{grid-template-columns:1fr 1fr;}
    .mini-cell:nth-child(3n){border-right:1px solid var(--line);} .mini-cell:nth-child(2n){border-right:none;}
    .mini-cell:nth-last-child(-n+3){border-bottom:1px solid var(--line);} .mini-cell:nth-last-child(-n+2){border-bottom:none;}
    .score-scale{grid-template-columns:1fr;}
}
</style>
    """

# v7.0 visual override is appended by wrapping load_css below.
_original_load_css = load_css

def load_css():
    base = _original_load_css()
    extra = r"""
<style>
/* v7.0 professional dashboard refinements */
.block-container{max-width:1540px!important;padding-top:.65rem!important;}
.app-topbar{position:sticky;top:0;z-index:30;background:rgba(255,255,255,.92);backdrop-filter:blur(10px);padding:10px 0 14px 0;}
.kpi-card{min-height:112px;border-radius:18px;box-shadow:0 12px 26px rgba(15,23,42,.055);}
.chart-stage{max-width:1240px;margin:12px auto 22px auto!important;padding:20px 22px 16px 22px!important;border-radius:22px!important;box-shadow:0 16px 38px rgba(15,23,42,.075)!important;}
.chart-header{border-bottom:1px solid #eef2f7;padding-bottom:10px;margin-bottom:10px!important;}
.chart-title{font-size:20px!important;}
.chart-caption{font-size:13px!important;}
.chart-story-card.pro-story{max-width:1240px;margin:12px auto 0 auto!important;background:#f8fbff!important;border-color:#dbeafe!important;}
.chart-story-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-top:10px;}
.chart-story-grid div{background:white;border:1px solid #e5e7eb;border-radius:12px;padding:10px;font-size:12px;color:#334155;}
.chart-story-grid b{font-size:10px;text-transform:uppercase;color:#64748b;letter-spacing:.05em;}
.chart-story-text{font-size:13px;color:#334155;line-height:1.55;margin-top:10px;}
.chart-progress-fill-good{height:9px;border-radius:999px;background:#059669;}
.chart-progress-fill-warn{height:9px;border-radius:999px;background:#d97706;}
.command-card{max-width:1240px;margin:0 auto 18px auto;border-radius:20px!important;}
.command-grid{grid-template-columns:1fr 1fr!important;}
.section-title{max-width:1240px;margin-left:auto!important;margin-right:auto!important;}
.section-subtitle{max-width:1240px;margin-left:auto!important;margin-right:auto!important;}
[data-testid="stRadio"] div[role="radiogroup"]{gap:18px!important;}
@media (max-width:900px){
    .chart-stage{padding:12px!important;border-radius:16px!important;margin:8px auto 14px auto!important;}
    .chart-title{font-size:16px!important;}
    .chart-story-grid{grid-template-columns:1fr 1fr;}
    .command-grid{grid-template-columns:1fr!important;}
    .kpi-card{margin-bottom:6px;}
}
</style>
"""
    return base + extra

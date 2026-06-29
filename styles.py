def load_css():
    return r"""
<style>
header, .stDeployButton, [data-testid='stToolbar'] {display:none!important;}
.block-container {padding:0.2rem 0.75rem 0.6rem 0.75rem!important;}
div[data-testid="stVerticalBlock"] {gap:0.32rem!important;}
div[data-testid="stHorizontalBlock"] {gap:0.55rem!important;}
h1 {font-size:22px!important;margin:0!important;}
h2 {font-size:18px!important;margin:0!important;}
h3 {font-size:15px!important;margin:0!important;}
[data-testid="stSidebar"] {min-width:255px;max-width:255px;}
[data-testid="stMetric"] {background:#fff;border:1px solid #e5e7eb;padding:6px 8px;border-radius:10px;}
[data-testid="stMetricLabel"] {font-size:11px!important;}
[data-testid="stMetricValue"] {font-size:18px!important;}
[data-testid="stMetricDelta"] {font-size:11px!important;}
.market-row {display:flex;justify-content:space-between;align-items:center;padding:5px 6px;border-bottom:1px solid #e5e7eb;font-size:12px;}
.hero-card {border:1px solid #111827;border-radius:16px;padding:18px;background:#111827;color:white;box-shadow:0 6px 18px rgba(17,24,39,.16);}
.hero-price {font-size:48px;font-weight:900;color:#10b981;font-family:monospace;line-height:1;margin-top:6px;margin-bottom:10px;}
.hero-title {font-size:12px;color:#d1d5db;text-transform:uppercase;font-weight:800;letter-spacing:.04em;}
.hero-text {font-size:13px;line-height:1.65;}
.white-card {border:1px solid #e5e7eb;border-radius:12px;padding:12px;background:#fff;}
.small-muted {font-size:12px;color:#6b7280;}
.badge {display:inline-flex;align-items:center;border-radius:999px;padding:4px 9px;font-size:11px;font-weight:900;margin:2px 0 8px 0;}
.badge-buy {background:#ecfdf5;color:#047857;border:1px solid #a7f3d0;}
.badge-wait {background:#fffbeb;color:#b45309;border:1px solid #fde68a;}
.badge-hold {background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;}
.kpi-grid {display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;}
.kpi-box {border:1px solid rgba(255,255,255,.18);border-radius:10px;padding:8px;background:rgba(255,255,255,.055);}
.kpi-label {font-size:10px;color:#9ca3af;text-transform:uppercase;font-weight:900;}
.kpi-value {font-size:16px;color:#fff;font-weight:900;margin-top:2px;}
.insight-card {border:1px solid #e5e7eb;border-radius:14px;padding:14px;background:#fff;min-height:150px;box-shadow:0 1px 4px rgba(0,0,0,.04);}
.insight-title {font-size:13px;font-weight:900;margin-bottom:6px;color:#111827;}
.insight-big {font-size:30px;font-weight:900;color:#111827;line-height:1.05;}
.insight-text {font-size:13px;line-height:1.55;color:#374151;}
.factor-card {border:1px solid #e5e7eb;border-radius:14px;padding:14px;background:#f9fafb;min-height:132px;}
.factor-head {font-size:13px;font-weight:900;color:#111827;margin-bottom:5px;}
.factor-body {font-size:13px;line-height:1.55;color:#374151;}
.dip-score {border:1px solid #e5e7eb;border-radius:14px;padding:14px;background:#fff;min-height:132px;}
.dip-score-big {font-size:34px;font-weight:900;color:#111827;line-height:1;}
.dip-label {font-size:11px;text-transform:uppercase;color:#6b7280;font-weight:900;letter-spacing:.04em;}
.deployment-card {border:1px solid #bbf7d0;border-radius:14px;padding:14px;background:#ecfdf5;min-height:132px;}
.deployment-big {font-size:30px;font-weight:900;color:#047857;line-height:1;}
.warning-card {border:1px solid #fde68a;border-radius:12px;padding:12px;background:#fffbeb;color:#92400e;}
.playbook-step {border:1px solid #e5e7eb;border-radius:14px;padding:14px;background:#ffffff;min-height:155px;}
.step-number {font-size:11px;color:#2563eb;text-transform:uppercase;font-weight:900;}
.step-title {font-size:15px;font-weight:900;color:#111827;margin:4px 0;}
.step-body {font-size:13px;line-height:1.55;color:#374151;}
.lesson-card {border:1px solid #e5e7eb;border-radius:12px;padding:12px;background:#fff;}
.style-card {border:1px solid #e5e7eb;border-radius:14px;padding:14px;background:#fff;min-height:155px;}
.style-title {font-size:14px;font-weight:900;color:#111827;}
.bar-bg {width:100%;height:8px;background:#e5e7eb;border-radius:999px;margin:8px 0;}
.bar-fill {height:8px;background:#2563eb;border-radius:999px;}
.regime-card {border:1px solid #dbeafe;border-radius:14px;padding:14px;background:#eff6ff;min-height:132px;}
.regime-big {font-size:30px;font-weight:900;color:#1d4ed8;line-height:1;}
.priority-card {border:1px solid #e5e7eb;border-radius:14px;padding:14px;background:#fff;min-height:145px;}
.priority-score {font-size:32px;font-weight:900;color:#111827;line-height:1;}
.live-card {border:1px solid #bfdbfe;border-radius:14px;padding:14px;background:#eff6ff;min-height:132px;}
.live-big {font-size:28px;font-weight:900;color:#1d4ed8;line-height:1;}
.journal-card {border:1px solid #e5e7eb;border-radius:14px;padding:14px;background:#f9fafb;}
@media (max-width:800px){
.block-container {padding:0.1rem 0.35rem 0.5rem 0.35rem!important;}
.hero-price {font-size:36px;}
[data-testid="stMetricValue"] {font-size:15px!important;}
.kpi-grid {grid-template-columns:1fr 1fr;}
.insight-card,.factor-card,.dip-score,.deployment-card,.playbook-step,.style-card {min-height:auto;}
}

.progress-bg {width:100%;height:12px;background:#e5e7eb;border-radius:999px;overflow:hidden;margin:8px 0;}
.progress-fill {height:12px;border-radius:999px;background:#2563eb;}
.progress-fill-good {height:12px;border-radius:999px;background:#10b981;}
.progress-fill-warn {height:12px;border-radius:999px;background:#f59e0b;}
.dynamic-strip {border:1px solid #dbeafe;background:#eff6ff;border-radius:14px;padding:12px;margin:6px 0;}
.sentiment-risk-on {border:1px solid #bbf7d0;background:#ecfdf5;color:#047857;border-radius:14px;padding:14px;}
.sentiment-neutral {border:1px solid #e5e7eb;background:#f9fafb;color:#374151;border-radius:14px;padding:14px;}
.sentiment-defensive {border:1px solid #fde68a;background:#fffbeb;color:#92400e;border-radius:14px;padding:14px;}
.sentiment-risk-off {border:1px solid #fecaca;background:#fef2f2;color:#991b1b;border-radius:14px;padding:14px;}
.sentiment-big {font-size:30px;font-weight:900;line-height:1;}
.timeline-item {border-left:4px solid #2563eb;padding:8px 12px;margin:8px 0;background:#fff;border-radius:0 10px 10px 0;border-top:1px solid #e5e7eb;border-right:1px solid #e5e7eb;border-bottom:1px solid #e5e7eb;}
.chart-note {font-size:12px;color:#6b7280;margin-top:-4px;}


.chart-note-card {border:1px solid #dbeafe;background:#eff6ff;border-radius:14px;padding:12px;margin:6px 0 12px 0;font-size:13px;line-height:1.55;color:#1f2937;}
.meaning-card {border:1px solid #e5e7eb;background:#ffffff;border-radius:14px;padding:12px;min-height:110px;}
.meaning-title {font-size:12px;text-transform:uppercase;color:#6b7280;font-weight:900;letter-spacing:.04em;}
.meaning-main {font-size:24px;font-weight:900;color:#111827;line-height:1.1;margin-top:4px;}
.meaning-text {font-size:13px;color:#374151;line-height:1.55;margin-top:6px;}
.score-scale {display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:8px;}
.score-scale div {font-size:11px;border:1px solid #e5e7eb;border-radius:8px;padding:6px;background:#f9fafb;text-align:center;}



/* v6.3 clean chart story */
.chart-story-card{
    background:#f8fafc;
    border:1px solid #dbeafe;
    border-radius:12px;
    padding:12px;
    margin-top:8px;
}
.chart-story-title{
    font-size:14px;
    font-weight:800;
    color:#0f172a;
    margin-bottom:8px;
}
.chart-story-text{
    font-size:13px;
    line-height:1.55;
    color:#334155;
    margin-top:8px;
    margin-bottom:6px;
}
.chart-progress-bg{
    width:100%;
    height:9px;
    border-radius:999px;
    background:#e5e7eb;
    overflow:hidden;
}
.chart-progress-fill{
    height:9px;
    border-radius:999px;
    background:#2563eb;
}


/* v6.5 chart-first layout */
.chart-solo-label{
    text-align:center;
    font-size:18px;
    font-weight:900;
    color:#111827;
    margin:10px 0 2px 0;
    letter-spacing:.01em;
}
.chart-solo-subtitle{
    text-align:center;
    font-size:12px;
    color:#6b7280;
    margin-bottom:8px;
}
.section-separator{
    height:1px;
    background:#e5e7eb;
    margin:14px 0;
}
.chart-stage-title{
    font-size:15px;
    font-weight:900;
    color:#111827;
    margin:8px 0 4px 0;
}

</style>
    """

# v6.2 additions are embedded via CSS string replacement below if load_css() returns a string.

# v6.5 chart-first refinements are returned inside load_css via runtime injection below.

# v6.6 separated dashboard layout injection
_old_load_css = load_css

def load_css():
    css = _old_load_css()
    extra = r"""
.chart-zone-title{
    text-align:center;
    font-size:20px;
    font-weight:950;
    color:#0f172a;
    margin:14px 0 2px 0;
    letter-spacing:.01em;
}
.chart-zone-subtitle{
    text-align:center;
    font-size:13px;
    color:#64748b;
    margin:0 auto 12px auto;
    max-width:950px;
    line-height:1.45;
}
.dashboard-section-title{
    font-size:16px;
    font-weight:950;
    color:#111827;
    margin:18px 0 8px 0;
    padding-top:4px;
    border-top:1px solid #e5e7eb;
}
.major-section-separator{
    height:18px;
    border-bottom:2px solid #e5e7eb;
    margin:10px 0 16px 0;
}
@media (max-width:800px){
    .chart-zone-title{font-size:17px;margin-top:8px;}
    .chart-zone-subtitle{font-size:12px;margin-bottom:8px;}
    .dashboard-section-title{font-size:14px;margin:12px 0 6px 0;}
}
"""
    return css.replace("</style>", extra + "\n</style>")

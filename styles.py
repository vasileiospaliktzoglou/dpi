def load_css():
    return """
    <style>
    .block-container {padding-top: 1.0rem; padding-bottom: 2rem; max-width: 1400px;}
    .metric-card, .decision-card, .warning-card, .buy-card, .wait-card, .neutral-card {
        background: white; border: 1px solid #E5E7EB; border-radius: 14px; padding: 16px;
        box-shadow: 0 1px 5px rgba(0,0,0,.05); min-height: 110px;
    }
    .buy-card {border-left: 6px solid #10B981; background:#ECFDF5;}
    .wait-card {border-left: 6px solid #F59E0B; background:#FFFBEB;}
    .warning-card {border-left: 6px solid #EF4444; background:#FEF2F2;}
    .neutral-card {border-left: 6px solid #3B82F6; background:#EFF6FF;}
    .label {font-size: 11px; color:#64748B; font-weight: 800; text-transform: uppercase; letter-spacing:.04em;}
    .big {font-size: 28px; font-weight: 900; color:#111827; line-height: 1.08; margin-top: 6px;}
    .small-muted {font-size: 12px; color:#6B7280; margin-top: 6px;}
    .market-row {display:flex; justify-content:space-between; padding:6px 2px; border-bottom:1px solid #EEF2F7; font-size:12px;}
    .section-note {background:#F8FAFC; border:1px solid #E5E7EB; border-radius:12px; padding:12px; color:#334155; font-size:13px;}
    .stDataFrame {font-size: 13px;}
    @media (max-width: 768px) {.big{font-size:22px;} .block-container{padding-left:.4rem; padding-right:.4rem;}}
    </style>
    """

"""
EXECUTE v6.10.3 - Internal Excel memory layer

The workbook is the application's private knowledge base, not a download/report.
It is automatically created, updated, backed up, and re-used by the intelligence
engine for future recommendations.
"""
from __future__ import annotations

from datetime import datetime, date
from pathlib import Path
from typing import Iterable, Dict, Any, List
import shutil

import pandas as pd

DATA_DIR = Path("data")
BACKUP_DIR = DATA_DIR / "backups"
REPORT_DIR = DATA_DIR / "reports"
WORKBOOK_PATH = DATA_DIR / "PALI_EXECUTE_DATA.xlsx"

SHEETS = {
    "dashboard": "Dashboard",
    "daily": "Daily_Intelligence",
    "recommendations": "Recommendations",
    "prices": "ETF_Prices",
    "features": "Feature_Store",
    "learning": "Learning",
    "reports": "Reports",
    "settings": "Settings",
}

ETF_UNIVERSE = ["V60A", "VNGA80", "VWCE"]


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today_key() -> str:
    return date.today().isoformat()


def _read_sheet(sheet: str) -> pd.DataFrame:
    if not WORKBOOK_PATH.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(WORKBOOK_PATH, sheet_name=sheet)
    except Exception:
        return pd.DataFrame()


def _upsert(existing: pd.DataFrame, rows: List[Dict[str, Any]], key_cols: List[str]) -> pd.DataFrame:
    incoming = pd.DataFrame(rows)
    if incoming.empty:
        return existing
    if existing.empty:
        return incoming

    existing = existing.copy()
    for col in incoming.columns:
        if col not in existing.columns:
            existing[col] = ""
    for col in existing.columns:
        if col not in incoming.columns:
            incoming[col] = ""

    existing["__key"] = existing[key_cols].astype(str).agg("|".join, axis=1)
    incoming["__key"] = incoming[key_cols].astype(str).agg("|".join, axis=1)
    existing = existing[~existing["__key"].isin(set(incoming["__key"]))]
    out = pd.concat([existing.drop(columns=["__key"]), incoming.drop(columns=["__key"])], ignore_index=True)
    return out


def _backup_once_per_day() -> None:
    if not WORKBOOK_PATH.exists():
        return
    stamp = datetime.now().strftime("%Y_%m_%d")
    backup = BACKUP_DIR / f"PALI_EXECUTE_DATA_{stamp}.xlsx"
    if not backup.exists():
        shutil.copy2(WORKBOOK_PATH, backup)


def _style_excel(writer: pd.ExcelWriter, dataframes: Dict[str, pd.DataFrame]) -> None:
    workbook = writer.book
    header_fmt = workbook.add_format({
        "bold": True,
        "font_color": "white",
        "bg_color": "#111827",
        "border": 1,
        "align": "center",
        "valign": "vcenter",
    })
    body_fmt = workbook.add_format({"border": 1, "valign": "top"})
    wrap_fmt = workbook.add_format({"border": 1, "valign": "top", "text_wrap": True})
    number_fmt = workbook.add_format({"border": 1, "num_format": "0.00", "valign": "top"})

    for sheet_name, worksheet in writer.sheets.items():
        df = dataframes.get(sheet_name)
        if df is None or df.empty:
            continue
        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, len(df), max(0, len(df.columns) - 1))
        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, header_fmt)
            sample = df[col_name].astype(str).head(200).tolist() + [str(col_name)]
            width = min(max(max(len(v) for v in sample) + 2, 10), 44)
            name = str(col_name).lower()
            if any(k in name for k in ["summary", "reason", "guardrail", "explanation", "drivers", "risks", "text", "html", "notes"]):
                worksheet.set_column(col_num, col_num, min(max(width, 28), 62), wrap_fmt)
            elif any(k in name for k in ["price", "target", "score", "confidence", "atr", "rsi", "pct"]):
                worksheet.set_column(col_num, col_num, width, number_fmt)
            else:
                worksheet.set_column(col_num, col_num, width, body_fmt)


def build_memory_rows(active_asset: str, state: dict, context, windows: Iterable, email: dict) -> Dict[str, pd.DataFrame]:
    generated_at = _now_stamp()
    run_date = _today_key()
    windows = list(windows)
    active_window = next((w for w in windows if getattr(w, "etf", None) == active_asset), windows[0] if windows else None)

    live_price = state.get("live_price", state.get("spot", ""))
    target = state.get("target", "")

    dashboard = pd.DataFrame([
        {"Metric": "Last updated", "Value": generated_at},
        {"Metric": "ETF universe", "Value": ", ".join(ETF_UNIVERSE)},
        {"Metric": "Active ETF", "Value": active_asset},
        {"Metric": "Market regime", "Value": getattr(context, "regime", "")},
        {"Metric": "Regime score", "Value": getattr(context, "score", "")},
        {"Metric": "Action", "Value": getattr(active_window, "action", "") if active_window else ""},
        {"Metric": "Best estimated window", "Value": getattr(active_window, "suggested_window", "") if active_window else ""},
        {"Metric": "Confidence", "Value": getattr(active_window, "confidence", "") if active_window else ""},
        {"Metric": "Target", "Value": target},
        {"Metric": "Live price", "Value": live_price},
        {"Metric": "Storage role", "Value": "Internal memory for future recommendations"},
    ])

    daily = [{
        "run_date": run_date,
        "active_etf": active_asset,
        "generated_at": generated_at,
        "market_regime": getattr(context, "regime", ""),
        "regime_score": getattr(context, "score", ""),
        "explanation": getattr(context, "explanation", ""),
        "tomorrow_bias": getattr(context, "tomorrow_bias", ""),
        "drivers": " | ".join(getattr(context, "drivers", []) or []),
        "risks": " | ".join(getattr(context, "risks", []) or []),
    }]

    recommendations = []
    features = []
    for w in windows:
        recommendations.append({
            "run_date": run_date,
            "etf": w.etf,
            "generated_at": generated_at,
            "role": w.role,
            "action": w.action,
            "best_estimated_window": w.suggested_window,
            "confidence": w.confidence,
            "reason": w.reason,
            "guardrail": w.guardrail,
            "outcome": "pending",
        })
        features.append({
            "run_date": run_date,
            "etf": w.etf,
            "generated_at": generated_at,
            "market_regime": getattr(context, "regime", ""),
            "regime_score": getattr(context, "score", ""),
            "vix": state.get("vix", ""),
            "atr": state.get("atr", ""),
            "rsi": state.get("rsi", ""),
            "live_price": live_price if w.etf == active_asset else "",
            "target": target if w.etf == active_asset else "",
            "decision": w.action,
            "confidence": w.confidence,
        })

    prices = [{
        "run_date": run_date,
        "etf": active_asset,
        "generated_at": generated_at,
        "target": target,
        "live_price": live_price,
        "live_change_pct": state.get("live_change_pct", ""),
        "atr": state.get("atr", ""),
        "decision": state.get("decision", getattr(active_window, "action", "") if active_window else ""),
    }]

    reports = [{
        "run_date": run_date,
        "report_type": "daily_intelligence",
        "generated_at": generated_at,
        "subject": email.get("subject", ""),
        "text": email.get("text", ""),
    }]

    learning = [{
        "run_date": run_date,
        "etf": active_asset,
        "generated_at": generated_at,
        "prediction": getattr(active_window, "action", "") if active_window else "",
        "actual_outcome": "pending_market_close_review",
        "correct": "pending",
        "notes": "Outcome to be evaluated after the next market session.",
    }]

    settings = pd.DataFrame([
        {"Setting": "Storage", "Value": "Excel workbook used internally as app memory"},
        {"Setting": "Workbook path", "Value": str(WORKBOOK_PATH)},
        {"Setting": "ETF universe", "Value": ", ".join(ETF_UNIVERSE)},
        {"Setting": "Excluded ETFs", "Value": "XEON, U03A"},
    ])

    return {
        SHEETS["dashboard"]: dashboard,
        SHEETS["daily"]: pd.DataFrame(daily),
        SHEETS["recommendations"]: pd.DataFrame(recommendations),
        SHEETS["prices"]: pd.DataFrame(prices),
        SHEETS["features"]: pd.DataFrame(features),
        SHEETS["learning"]: pd.DataFrame(learning),
        SHEETS["reports"]: pd.DataFrame(reports),
        SHEETS["settings"]: settings,
    }


def save_daily_intelligence(active_asset: str, state: dict, context, windows: Iterable, email: dict) -> Path:
    """Upsert today's intelligence into the internal Excel memory workbook."""
    _ensure_dirs()
    _backup_once_per_day()
    new = build_memory_rows(active_asset, state, context, windows, email)

    dataframes = {
        SHEETS["dashboard"]: new[SHEETS["dashboard"]],
        SHEETS["daily"]: _upsert(_read_sheet(SHEETS["daily"]), new[SHEETS["daily"]].to_dict("records"), ["run_date", "active_etf"]),
        SHEETS["recommendations"]: _upsert(_read_sheet(SHEETS["recommendations"]), new[SHEETS["recommendations"]].to_dict("records"), ["run_date", "etf"]),
        SHEETS["prices"]: _upsert(_read_sheet(SHEETS["prices"]), new[SHEETS["prices"]].to_dict("records"), ["run_date", "etf"]),
        SHEETS["features"]: _upsert(_read_sheet(SHEETS["features"]), new[SHEETS["features"]].to_dict("records"), ["run_date", "etf"]),
        SHEETS["learning"]: _upsert(_read_sheet(SHEETS["learning"]), new[SHEETS["learning"]].to_dict("records"), ["run_date", "etf"]),
        SHEETS["reports"]: _upsert(_read_sheet(SHEETS["reports"]), new[SHEETS["reports"]].to_dict("records"), ["run_date", "report_type"]),
        SHEETS["settings"]: new[SHEETS["settings"]],
    }

    with pd.ExcelWriter(WORKBOOK_PATH, engine="xlsxwriter") as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        _style_excel(writer, dataframes)

    return WORKBOOK_PATH


def workbook_status() -> dict:
    _ensure_dirs()
    exists = WORKBOOK_PATH.exists()
    return {
        "path": str(WORKBOOK_PATH),
        "exists": exists,
        "size_kb": round(WORKBOOK_PATH.stat().st_size / 1024, 1) if exists else 0,
        "backup_dir": str(BACKUP_DIR),
        "mode": "internal_memory",
    }

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, Any
import datetime as dt

import pandas as pd
from openpyxl import Workbook, load_workbook

from config import MEMORY_FILE, DATA_DIR

SHEETS = ["Runs", "ETF_Decisions", "Market_Summary", "Learning", "Feature_Store"]


def _safe_cell(value: Any) -> Any:
    """Convert values so Excel never receives lists, dicts, NaN, or unsupported objects.

    This explicitly avoids the earlier 'object of type float has no len()' style error by
    not calling len() on arbitrary values.
    """
    if value is None:
        return ""
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return float(value)
    if isinstance(value, (int, str, bool)):
        return value
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        return "; ".join(str(x) for x in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in value.items())
    return str(value)


def ensure_workbook() -> Path:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    path = Path(MEMORY_FILE)
    if not path.exists():
        wb = Workbook()
        ws = wb.active
        ws.title = SHEETS[0]
        for name in SHEETS[1:]:
            wb.create_sheet(name)
        headers = {
            "Runs": ["run_id", "timestamp", "version", "primary_etf", "primary_action"],
            "ETF_Decisions": ["run_id", "timestamp", "etf", "action", "live_price", "target_price", "gap_pct", "confidence", "target_touch_1d", "target_touch_5d", "reason"],
            "Market_Summary": ["run_id", "timestamp", "regime", "score", "summary", "drivers"],
            "Learning": ["run_id", "timestamp", "note"],
            "Feature_Store": ["run_id", "timestamp", "etf", "atr", "rsi", "trend", "market_regime", "market_score", "gap_pct", "decision"],
        }
        for sheet, cols in headers.items():
            wb[sheet].append(cols)
        wb.save(path)
    return path


def append_rows(sheet_name: str, rows: Iterable[dict]) -> None:
    path = ensure_workbook()
    wb = load_workbook(path)
    if sheet_name not in wb.sheetnames:
        wb.create_sheet(sheet_name)
    ws = wb[sheet_name]
    existing_headers = [c.value for c in ws[1]] if ws.max_row >= 1 else []
    rows = list(rows)
    if not rows:
        wb.save(path)
        return
    headers = existing_headers or list(rows[0].keys())
    if not existing_headers:
        ws.append(headers)
    for row in rows:
        ws.append([_safe_cell(row.get(h, "")) for h in headers])
    wb.save(path)


def save_run(version: str, market, decisions: Dict[str, Any], primary) -> None:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_id = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    append_rows("Runs", [{"run_id": run_id, "timestamp": now, "version": version, "primary_etf": primary.symbol, "primary_action": primary.action}])
    append_rows("Market_Summary", [{"run_id": run_id, "timestamp": now, "regime": market.regime, "score": market.score, "summary": market.one_sentence, "drivers": market.drivers}])
    append_rows("ETF_Decisions", [{
        "run_id": run_id, "timestamp": now, "etf": d.symbol, "action": d.action, "live_price": d.live_price,
        "target_price": d.target_price, "gap_pct": d.gap_pct, "confidence": d.confidence_label,
        "target_touch_1d": d.target_touch_1d, "target_touch_5d": d.target_touch_5d, "reason": d.reason,
    } for d in decisions.values()])
    append_rows("Feature_Store", [{
        "run_id": run_id, "timestamp": now, "etf": d.symbol, "atr": d.atr, "rsi": d.rsi, "trend": d.trend,
        "market_regime": market.regime, "market_score": market.score, "gap_pct": d.gap_pct, "decision": d.action,
    } for d in decisions.values()])


def status() -> str:
    path = ensure_workbook()
    return f"Internal Excel memory active: {path}"

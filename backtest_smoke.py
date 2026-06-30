from engine import build_decisions, choose_primary
from excel_memory import save_run, ensure_workbook
from config import APP_VERSION, ETFS


def main():
    market, decisions = build_decisions()
    assert set(decisions.keys()) == set(ETFS.keys())
    assert "XEON" not in decisions and "U03A" not in decisions
    for symbol, d in decisions.items():
        assert d.live_price > 0, symbol
        assert d.target_price > 0, symbol
        assert d.history is not None and len(d.history) > 30, symbol
    primary = choose_primary(decisions)
    save_run(APP_VERSION, market, decisions, primary)
    assert ensure_workbook().exists()
    print("Smoke test passed")


if __name__ == "__main__":
    main()

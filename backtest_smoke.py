from engine import build_decisions, choose_primary
from excel_memory import save_run, status
from config import APP_VERSION

market, decisions = build_decisions()
primary = choose_primary(decisions)
save_run(APP_VERSION, market, decisions, primary)
assert set(decisions.keys()) == {"V60A", "VNGA80", "VWCE"}
for d in decisions.values():
    assert d.live_price > 0
    assert d.target_price > 0
    assert 0 <= d.target_touch_1d <= 100
    assert 0 <= d.target_touch_5d <= 100
print("SMOKE TEST PASSED")
print(primary.symbol, primary.action)
print(status())

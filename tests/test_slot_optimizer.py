from smartpark.db import get_connection, init_db
from smartpark.services.slot_optimizer import find_best_slot


def test_optimizer_selects_compatible_available_ev_slot(tmp_path, monkeypatch):
    monkeypatch.setenv("SMARTPARK_DB_PATH", str(tmp_path / "optimizer.db"))
    init_db(reset=True, seed=True)
    with get_connection() as conn:
        result = find_best_slot(conn, "EV", None)
    assert result["slot"] is not None
    assert result["slot"]["slot_type"] in ["EV", "VIP"]
    assert result["score_breakdown"]["compatibility_penalty"] == 0


def test_optimizer_returns_no_slot_when_zone_has_no_compatible_space(tmp_path, monkeypatch):
    monkeypatch.setenv("SMARTPARK_DB_PATH", str(tmp_path / "optimizer_none.db"))
    init_db(reset=True, seed=True)
    with get_connection() as conn:
        result = find_best_slot(conn, "Truck", "zone_a")
    assert result["slot"] is None
    assert result["candidates_considered"] >= 1

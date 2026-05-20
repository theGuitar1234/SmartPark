from smartpark.services.tariff_service import TariffSnapshot, calculate_fee


def test_fee_inside_grace_period_is_zero():
    tariff = TariffSnapshot(hourly_rate=2.5, grace_minutes=15, daily_max=18)
    fee = calculate_fee("2026-01-01T10:00:00Z", "2026-01-01T10:10:00Z", tariff)
    assert fee == 0


def test_fee_rounds_up_to_next_hour_after_grace():
    tariff = TariffSnapshot(hourly_rate=2.5, grace_minutes=15, daily_max=18)
    fee = calculate_fee("2026-01-01T10:00:00Z", "2026-01-01T11:16:00Z", tariff)
    assert fee == 5.0


def test_fee_applies_daily_max():
    tariff = TariffSnapshot(hourly_rate=5, grace_minutes=0, daily_max=20)
    fee = calculate_fee("2026-01-01T00:00:00Z", "2026-01-01T12:01:00Z", tariff)
    assert fee == 20


def test_exit_before_entry_is_rejected():
    tariff = TariffSnapshot(hourly_rate=5, grace_minutes=0, daily_max=20)
    try:
        calculate_fee("2026-01-01T10:00:00Z", "2026-01-01T09:59:00Z", tariff)
    except ValueError as ex:
        assert "Exit time" in str(ex)
    else:
        raise AssertionError("Invalid time ordering was not rejected")

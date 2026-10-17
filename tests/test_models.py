import datetime

import pydantic
import pytest

from alphaessaio.models import (
    ChargeConfig,
    EssSystem,
    EvChargerStatus,
    PowerSample,
)

_VALID_CHARGE_CONFIG = {
    "batHighCap": 100,
    "gridCharge": 1,
    "timeChaf1": "01:15",
    "timeChae1": "06:00",
    "timeChaf2": "00:00",
    "timeChae2": "23:45",
}


def test_charge_config_parses_api_times_and_flags():
    config = ChargeConfig.model_validate(_VALID_CHARGE_CONFIG)

    assert config.time_chaf1 == datetime.time(1, 15)
    assert config.grid_charge is True


def test_charge_config_dumps_back_to_api_format():
    config = ChargeConfig.model_validate(_VALID_CHARGE_CONFIG)

    assert config.model_dump(by_alias=True) == {
        **_VALID_CHARGE_CONFIG,
        "batHighCap": 100.0,
    }


@pytest.mark.parametrize("off_grid_time", ["01:10", "23:59", "12:00:30"])
def test_charge_config_rejects_times_outside_quarter_hour_grid(off_grid_time):
    with pytest.raises(pydantic.ValidationError, match="15 minute grid"):
        ChargeConfig.model_validate(
            {**_VALID_CHARGE_CONFIG, "timeChaf1": off_grid_time}
        )


@pytest.mark.parametrize("battery_capacity_field", ["cobat", "cbat"])
def test_ess_system_accepts_both_battery_capacity_spellings(battery_capacity_field):
    system = EssSystem.model_validate(
        {"sysSn": "AL0000000000000", battery_capacity_field: 10.1}
    )

    assert system.cobat == 10.1


def test_power_sample_accepts_documented_charging_pile_spelling():
    sample = PowerSample.model_validate(
        {
            "sysSn": "AL0000000000000",
            "uploadTime": "2024-06-01 12:00:00",
            "pChargingPile": 7400,
        }
    )

    assert sample.pcharging_pile == 7400


def test_model_keeps_unknown_fields_instead_of_failing():
    system = EssSystem.model_validate(
        {"sysSn": "AL0000000000000", "brandNewField": "x"}
    )

    assert system.model_extra == {"brandNewField": "x"}


def test_ev_charger_status_keeps_unknown_state_code():
    status = EvChargerStatus.model_validate({"evchargerStatus": 7})

    assert status.evcharger_status == 7

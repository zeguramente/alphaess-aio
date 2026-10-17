import datetime

import pytest

from alphaessaio.models import (
    ChargeConfig,
    ControlMode,
    DailyEnergy,
    DischargeConfig,
    EssSystem,
    EvCharger,
    EvChargerCurrent,
    EvChargerState,
    EvChargerStatus,
    LastPowerData,
    PowerSample,
    SystemSummary,
)
from tests.conftest import FakeResponse
from tests.helpers import FIXTURE_EVCHARGER_SN, FIXTURE_SYS_SN

QUERY_DATE = datetime.date(2024, 6, 1)


_GET_CASES = [
    ("get_ess_list", {}, "getEssList", {}, EssSystem),
    (
        "get_last_power_data",
        {"sys_sn": FIXTURE_SYS_SN},
        "getLastPowerData",
        {"sysSn": FIXTURE_SYS_SN},
        LastPowerData,
    ),
    (
        "get_one_day_power_by_sn",
        {"sys_sn": FIXTURE_SYS_SN, "query_date": QUERY_DATE},
        "getOneDayPowerBySn",
        {"sysSn": FIXTURE_SYS_SN, "queryDate": "2024-06-01"},
        PowerSample,
    ),
    (
        "get_one_date_energy_by_sn",
        {"sys_sn": FIXTURE_SYS_SN, "query_date": QUERY_DATE},
        "getOneDateEnergyBySn",
        {"sysSn": FIXTURE_SYS_SN, "queryDate": "2024-06-01"},
        DailyEnergy,
    ),
    (
        "get_sum_data_for_customer",
        {"sys_sn": FIXTURE_SYS_SN},
        "getSumDataForCustomer",
        {"sysSn": FIXTURE_SYS_SN},
        SystemSummary,
    ),
    (
        "get_charge_config_info",
        {"sys_sn": FIXTURE_SYS_SN},
        "getChargeConfigInfo",
        {"sysSn": FIXTURE_SYS_SN},
        ChargeConfig,
    ),
    (
        "get_dis_charge_config_info",
        {"sys_sn": FIXTURE_SYS_SN},
        "getDisChargeConfigInfo",
        {"sysSn": FIXTURE_SYS_SN},
        DischargeConfig,
    ),
    (
        "get_ev_charger_currents_by_sn",
        {"sys_sn": FIXTURE_SYS_SN},
        "getEvChargerCurrentsBySn",
        {"sysSn": FIXTURE_SYS_SN},
        EvChargerCurrent,
    ),
    (
        "get_ev_charger_status_by_sn",
        {"sys_sn": FIXTURE_SYS_SN, "evcharger_sn": FIXTURE_EVCHARGER_SN},
        "getEvChargerStatusBySn",
        {"sysSn": FIXTURE_SYS_SN, "evchargerSn": FIXTURE_EVCHARGER_SN},
        EvChargerStatus,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "kwargs", "endpoint", "expected_query", "expected_type"),
    _GET_CASES,
    ids=[case[0] for case in _GET_CASES],
)
async def test_get_endpoint_sends_query_and_parses_fixture(
    api, fake_cloud, method_name, kwargs, endpoint, expected_query, expected_type
):
    result = await getattr(api, method_name)(**kwargs)

    sent = fake_cloud.last_request()
    assert (sent.method, sent.endpoint, sent.query) == ("GET", endpoint, expected_query)
    parsed_items = result if isinstance(result, list) else [result]
    assert parsed_items
    assert all(isinstance(item, expected_type) for item in parsed_items)
    assert not any(item.model_extra for item in parsed_items)


async def test_get_last_power_data_maps_nested_details(api):
    power = await api.get_last_power_data(FIXTURE_SYS_SN)

    assert power.pgrid == 3230.0
    assert power.pgrid_detail.pmeter_l1 == 1199.0
    assert power.ppv_detail.pmeter_dc == 0.0
    assert power.pev_detail.ev1_power is None


async def test_get_one_day_power_returns_samples_newest_first(api):
    samples = await api.get_one_day_power_by_sn(FIXTURE_SYS_SN, QUERY_DATE)

    upload_times = [sample.upload_time for sample in samples]
    assert upload_times == sorted(upload_times, reverse=True)


async def test_get_ev_charger_config_list_without_charger_is_empty(api, fake_cloud):
    chargers = await api.get_ev_charger_config_list(FIXTURE_SYS_SN)

    assert chargers == []
    assert fake_cloud.last_request().query == {"sysSn": FIXTURE_SYS_SN}


async def test_get_ev_charger_config_list_parses_chargers(api, fake_cloud):
    fake_cloud.responses["getEvChargerConfigList"] = FakeResponse(
        {
            "code": 200,
            "msg": "Success",
            "data": [
                {"evchargerSn": FIXTURE_EVCHARGER_SN, "evchargerModel": "SMILE-EVCT11"}
            ],
        }
    )

    (charger,) = await api.get_ev_charger_config_list(FIXTURE_SYS_SN)

    assert charger == EvCharger(
        evcharger_sn=FIXTURE_EVCHARGER_SN, evcharger_model="SMILE-EVCT11"
    )


async def test_get_ev_charger_status_maps_state_enum(api):
    (status,) = await api.get_ev_charger_status_by_sn(
        FIXTURE_SYS_SN, FIXTURE_EVCHARGER_SN
    )

    assert status.evcharger_status is EvChargerState.CHARGING


_CHARGE_CONFIG = ChargeConfig(
    bat_high_cap=95,
    grid_charge=True,
    time_chaf1=datetime.time(1, 30),
    time_chae1=datetime.time(5, 45),
    time_chaf2=datetime.time(0, 0),
    time_chae2=datetime.time(0, 0),
)
_DISCHARGE_CONFIG = DischargeConfig(
    bat_use_cap=15,
    ctr_dis=False,
    time_disf1=datetime.time(17, 0),
    time_dise1=datetime.time(23, 45),
    time_disf2=datetime.time(0, 0),
    time_dise2=datetime.time(0, 0),
)


_POST_CASES = [
    (
        "update_charge_config_info",
        {"sys_sn": FIXTURE_SYS_SN, "config": _CHARGE_CONFIG},
        "updateChargeConfigInfo",
        {
            "sysSn": FIXTURE_SYS_SN,
            "batHighCap": 95.0,
            "gridCharge": 1,
            "timeChaf1": "01:30",
            "timeChae1": "05:45",
            "timeChaf2": "00:00",
            "timeChae2": "00:00",
        },
    ),
    (
        "update_dis_charge_config_info",
        {"sys_sn": FIXTURE_SYS_SN, "config": _DISCHARGE_CONFIG},
        "updateDisChargeConfigInfo",
        {
            "sysSn": FIXTURE_SYS_SN,
            "batUseCap": 15.0,
            "ctrDis": 0,
            "timeDisf1": "17:00",
            "timeDise1": "23:45",
            "timeDisf2": "00:00",
            "timeDise2": "00:00",
        },
    ),
    (
        "set_ev_charger_currents_by_sn",
        {"sys_sn": FIXTURE_SYS_SN, "currentsetting": 16.0},
        "setEvChargerCurrentsBySn",
        {"sysSn": FIXTURE_SYS_SN, "currentsetting": 16.0},
    ),
    (
        "remote_control_ev_charger",
        {
            "sys_sn": FIXTURE_SYS_SN,
            "evcharger_sn": FIXTURE_EVCHARGER_SN,
            "control_mode": ControlMode.START_CHARGING,
        },
        "remoteControlEvCharger",
        {
            "sysSn": FIXTURE_SYS_SN,
            "evchargerSn": FIXTURE_EVCHARGER_SN,
            "controlMode": 1,
        },
    ),
    (
        "bind_sn",
        {"sys_sn": FIXTURE_SYS_SN, "code": "123456"},
        "bindSn",
        {"sysSn": FIXTURE_SYS_SN, "code": "123456"},
    ),
    (
        "un_bind_sn",
        {"sys_sn": FIXTURE_SYS_SN},
        "unBindSn",
        {"sysSn": FIXTURE_SYS_SN},
    ),
]


@pytest.mark.parametrize(
    ("method_name", "kwargs", "endpoint", "expected_body"),
    _POST_CASES,
    ids=[case[0] for case in _POST_CASES],
)
async def test_post_endpoint_sends_json_body(
    api, fake_cloud, method_name, kwargs, endpoint, expected_body
):
    result = await getattr(api, method_name)(**kwargs)

    sent = fake_cloud.last_request()
    assert result is None
    assert (sent.method, sent.endpoint) == ("POST", endpoint)
    assert sent.json_body == expected_body


async def test_get_verification_code_sends_check_code(api, fake_cloud):
    await api.get_verification_code(FIXTURE_SYS_SN, "ABCDE")

    assert fake_cloud.last_request().query == {
        "sysSn": FIXTURE_SYS_SN,
        "checkCode": "ABCDE",
    }

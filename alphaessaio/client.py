"""Typed client for all AlphaESS Open API endpoints."""

import datetime

from pydantic import TypeAdapter

from alphaessaio.models import (
    ChargeConfig,
    ControlMode,
    DailyEnergy,
    DischargeConfig,
    EssSystem,
    EvCharger,
    EvChargerCurrent,
    EvChargerStatus,
    LastPowerData,
    PowerSample,
    SystemSummary,
)
from alphaessaio.transport import AlphaEssTransport

_ESS_SYSTEMS = TypeAdapter(list[EssSystem])
_POWER_SAMPLES = TypeAdapter(list[PowerSample])
_EV_CHARGERS = TypeAdapter(list[EvCharger])
_EV_CHARGER_STATUSES = TypeAdapter(list[EvChargerStatus])


def _format_query_date(query_date: datetime.date) -> str:
    return query_date.strftime("%Y-%m-%d")


class AlphaEssAPI(AlphaEssTransport):
    """Client for the AlphaESS Open API.

    Use it as async context manager, or pass Home Assistant's shared session::

        api = AlphaEssAPI(auth, session=async_get_clientsession(hass))

    All methods raise the exceptions from ``alphaessaio.exceptions``.
    """

    async def get_ess_list(self) -> list[EssSystem]:
        """Get all systems bound to the developer account."""
        return _ESS_SYSTEMS.validate_python(await self._request("GET", "getEssList"))

    async def get_last_power_data(self, sys_sn: str) -> LastPowerData:
        """Get the most recent real-time power snapshot.

        Args:
            sys_sn: System serial number.
        """
        data = await self._request("GET", "getLastPowerData", {"sysSn": sys_sn})
        return LastPowerData.model_validate(data)

    async def get_one_day_power_by_sn(
        self, sys_sn: str, query_date: datetime.date
    ) -> list[PowerSample]:
        """Get the power curve of one day in 5 minute samples, newest first.

        Args:
            sys_sn: System serial number.
            query_date: Day to fetch.
        """
        data = await self._request(
            "GET",
            "getOneDayPowerBySn",
            {"sysSn": sys_sn, "queryDate": _format_query_date(query_date)},
        )
        return _POWER_SAMPLES.validate_python(data)

    async def get_one_date_energy_by_sn(
        self, sys_sn: str, query_date: datetime.date
    ) -> DailyEnergy:
        """Get the energy totals of one day.

        Args:
            sys_sn: System serial number.
            query_date: Day to fetch.
        """
        data = await self._request(
            "GET",
            "getOneDateEnergyBySn",
            {"sysSn": sys_sn, "queryDate": _format_query_date(query_date)},
        )
        return DailyEnergy.model_validate(data)

    async def get_sum_data_for_customer(self, sys_sn: str) -> SystemSummary:
        """Get aggregated energy and income figures.

        Args:
            sys_sn: System serial number.
        """
        data = await self._request("GET", "getSumDataForCustomer", {"sysSn": sys_sn})
        return SystemSummary.model_validate(data)

    async def get_charge_config_info(self, sys_sn: str) -> ChargeConfig:
        """Get the grid charging settings.

        Args:
            sys_sn: System serial number.
        """
        data = await self._request("GET", "getChargeConfigInfo", {"sysSn": sys_sn})
        return ChargeConfig.model_validate(data)

    async def update_charge_config_info(
        self, sys_sn: str, config: ChargeConfig
    ) -> None:
        """Change the grid charging settings.

        AlphaESS allows changing these settings only about once per day.

        Args:
            sys_sn: System serial number.
            config: New settings, e.g. a modified copy of
                ``get_charge_config_info`` via ``model_copy(update=...)``.
        """
        await self._request(
            "POST",
            "updateChargeConfigInfo",
            {"sysSn": sys_sn, **config.model_dump(by_alias=True)},
        )

    async def get_dis_charge_config_info(self, sys_sn: str) -> DischargeConfig:
        """Get the battery discharge settings.

        Args:
            sys_sn: System serial number.
        """
        data = await self._request("GET", "getDisChargeConfigInfo", {"sysSn": sys_sn})
        return DischargeConfig.model_validate(data)

    async def update_dis_charge_config_info(
        self, sys_sn: str, config: DischargeConfig
    ) -> None:
        """Change the battery discharge settings.

        AlphaESS allows changing these settings only about once per day.

        Args:
            sys_sn: System serial number.
            config: New settings.
        """
        await self._request(
            "POST",
            "updateDisChargeConfigInfo",
            {"sysSn": sys_sn, **config.model_dump(by_alias=True)},
        )

    async def get_ev_charger_config_list(self, sys_sn: str) -> list[EvCharger]:
        """Get the EV chargers registered at a system.

        Args:
            sys_sn: System serial number.
        """
        data = await self._request("GET", "getEvChargerConfigList", {"sysSn": sys_sn})
        return _EV_CHARGERS.validate_python(data)

    async def get_ev_charger_currents_by_sn(self, sys_sn: str) -> EvChargerCurrent:
        """Get the household current limit used for EV charging.

        Args:
            sys_sn: System serial number.
        """
        data = await self._request("GET", "getEvChargerCurrentsBySn", {"sysSn": sys_sn})
        return EvChargerCurrent.model_validate(data)

    async def set_ev_charger_currents_by_sn(
        self, sys_sn: str, currentsetting: float
    ) -> None:
        """Set the household current limit used for EV charging.

        Args:
            sys_sn: System serial number.
            currentsetting: Household current limit in A.
        """
        await self._request(
            "POST",
            "setEvChargerCurrentsBySn",
            {"sysSn": sys_sn, "currentsetting": currentsetting},
        )

    async def get_ev_charger_status_by_sn(
        self, sys_sn: str, evcharger_sn: str
    ) -> list[EvChargerStatus]:
        """Get the charging state of an EV charger.

        Args:
            sys_sn: System serial number.
            evcharger_sn: Serial number of the EV charger.
        """
        data = await self._request(
            "GET",
            "getEvChargerStatusBySn",
            {"sysSn": sys_sn, "evchargerSn": evcharger_sn},
        )
        return _EV_CHARGER_STATUSES.validate_python(data)

    async def remote_control_ev_charger(
        self, sys_sn: str, evcharger_sn: str, control_mode: ControlMode
    ) -> None:
        """Start or stop charging at an EV charger.

        Args:
            sys_sn: System serial number.
            evcharger_sn: Serial number of the EV charger.
            control_mode: Whether to start or stop charging.
        """
        await self._request(
            "POST",
            "remoteControlEvCharger",
            {
                "sysSn": sys_sn,
                "evchargerSn": evcharger_sn,
                "controlMode": int(control_mode),
            },
        )

    async def get_verification_code(self, sys_sn: str, check_code: str) -> None:
        """Request the verification code needed to bind a system.

        Args:
            sys_sn: System serial number.
            check_code: Check code printed on the system.
        """
        await self._request(
            "GET", "getVerificationCode", {"sysSn": sys_sn, "checkCode": check_code}
        )

    async def bind_sn(self, sys_sn: str, code: str) -> None:
        """Bind a system to the developer account.

        Args:
            sys_sn: System serial number.
            code: Verification code from ``get_verification_code``.
        """
        await self._request("POST", "bindSn", {"sysSn": sys_sn, "code": code})

    async def un_bind_sn(self, sys_sn: str) -> None:
        """Unbind a system from the developer account.

        Args:
            sys_sn: System serial number.
        """
        await self._request("POST", "unBindSn", {"sysSn": sys_sn})

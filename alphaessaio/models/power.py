"""Models for real-time power and daily energy data."""

import datetime

from pydantic import AliasChoices, Field

from alphaessaio.models._base import AlphaEssModel


class PvPowerDetail(AlphaEssModel):
    """Power per PV string in W."""

    ppv1: float | None = None
    ppv2: float | None = None
    ppv3: float | None = None
    ppv4: float | None = None
    pmeter_dc: float | None = None


class GridPowerDetail(AlphaEssModel):
    """Grid meter power per phase in W."""

    pmeter_l1: float | None = None
    pmeter_l2: float | None = None
    pmeter_l3: float | None = None


class EvPowerDetail(AlphaEssModel):
    """Power per EV charger in W."""

    ev1_power: float | None = None
    ev2_power: float | None = None
    ev3_power: float | None = None
    ev4_power: float | None = None


class LastPowerData(AlphaEssModel):
    """Most recent real-time power snapshot of a system (getLastPowerData).

    Attributes:
        ppv: Total PV power in W.
        pload: Load power in W.
        soc: Battery state of charge in percent.
        pgrid: Grid power in W; positive means import, negative means export.
        pbat: Battery power in W.
        preal_l1: Inverter output power on phase L1 in W.
        preal_l2: Inverter output power on phase L2 in W.
        preal_l3: Inverter output power on phase L3 in W.
        pev: Total EV charger power in W.
    """

    ppv: float | None = None
    ppv_detail: PvPowerDetail | None = None
    pload: float | None = None
    soc: float | None = None
    pgrid: float | None = None
    pgrid_detail: GridPowerDetail | None = None
    pbat: float | None = None
    preal_l1: float | None = None
    preal_l2: float | None = None
    preal_l3: float | None = None
    pev: float | None = None
    pev_detail: EvPowerDetail | None = None


class PowerSample(AlphaEssModel):
    """One sample of the intraday power curve (getOneDayPowerBySn).

    Attributes:
        sys_sn: System serial number.
        upload_time: Time the sample was recorded.
        ppv: PV power in W.
        load: Load power in W.
        cbat: Battery state of charge in percent.
        feed_in: Grid feed-in power in W.
        grid_charge: Grid import power in W.
        pcharging_pile: EV charger power in W.
    """

    sys_sn: str
    upload_time: datetime.datetime
    ppv: float | None = None
    load: float | None = None
    cbat: float | None = Field(
        default=None, validation_alias=AliasChoices("cbat", "cobat")
    )
    feed_in: float | None = None
    grid_charge: float | None = None
    pcharging_pile: float | None = Field(
        default=None, validation_alias=AliasChoices("pchargingPile", "pChargingPile")
    )


class DailyEnergy(AlphaEssModel):
    """Energy totals of a single day (getOneDateEnergyBySn).

    Attributes:
        sys_sn: System serial number.
        the_date: Day the totals belong to, as returned by the API.
        epv: PV generation in kWh.
        e_input: Grid consumption in kWh.
        e_output: Grid feed-in in kWh.
        e_charge: Battery charge in kWh.
        e_discharge: Battery discharge in kWh.
        e_grid_charge: Battery charge from the grid in kWh.
        e_charging_pile: EV charger consumption in kWh.
    """

    sys_sn: str
    the_date: str | None = None
    epv: float | None = None
    e_input: float | None = None
    e_output: float | None = None
    e_charge: float | None = None
    e_discharge: float | None = None
    e_grid_charge: float | None = None
    e_charging_pile: float | None = None

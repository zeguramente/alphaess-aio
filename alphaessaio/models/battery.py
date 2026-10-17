"""Models for the battery charge and discharge time windows."""

import datetime
from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from alphaessaio.models._base import AlphaEssModel

_TIME_STEP_MINUTES = 15


def _ensure_quarter_hour(value: datetime.time) -> datetime.time:
    # The API silently ignores times outside the 15 minute grid.
    if value.minute % _TIME_STEP_MINUTES or value.second or value.microsecond:
        raise ValueError(
            f"{value} is not on the {_TIME_STEP_MINUTES} minute grid (00:00-23:45)"
        )
    return value


QuarterHour = Annotated[
    datetime.time,
    AfterValidator(_ensure_quarter_hour),
    PlainSerializer(lambda value: value.strftime("%H:%M"), return_type=str),
]
"""Time of day on the 15 minute grid, sent to the API as ``HH:mm``."""

_FlagAsInt = Annotated[bool, PlainSerializer(int, return_type=int)]


class ChargeConfig(AlphaEssModel):
    """Grid charging settings (getChargeConfigInfo / updateChargeConfigInfo).

    Attributes:
        bat_high_cap: State of charge in percent at which charging stops.
        grid_charge: Whether charging the battery from the grid is enabled.
        time_chaf1: Start of charging period 1.
        time_chae1: End of charging period 1.
        time_chaf2: Start of charging period 2.
        time_chae2: End of charging period 2.
    """

    bat_high_cap: float
    grid_charge: _FlagAsInt
    time_chaf1: QuarterHour
    time_chae1: QuarterHour
    time_chaf2: QuarterHour
    time_chae2: QuarterHour


class DischargeConfig(AlphaEssModel):
    """Battery discharge settings (getDisChargeConfigInfo / updateDisChargeConfigInfo).

    Attributes:
        bat_use_cap: State of charge in percent at which discharging stops.
        ctr_dis: Whether the discharge time control is enabled.
        time_disf1: Start of discharging period 1.
        time_dise1: End of discharging period 1.
        time_disf2: Start of discharging period 2.
        time_dise2: End of discharging period 2.
    """

    bat_use_cap: float
    ctr_dis: _FlagAsInt
    time_disf1: QuarterHour
    time_dise1: QuarterHour
    time_disf2: QuarterHour
    time_dise2: QuarterHour

"""Models for EV chargers connected to a system."""

from enum import IntEnum

from pydantic import Field

from alphaessaio.models._base import AlphaEssModel


class EvChargerState(IntEnum):
    """Charging state reported by getEvChargerStatusBySn."""

    AVAILABLE = 1
    PREPARING = 2
    CHARGING = 3
    SUSPENDED_EVSE = 4
    SUSPENDED_EV = 5
    FINISHING = 6
    FAULTED = 9


class ControlMode(IntEnum):
    """Command for remoteControlEvCharger."""

    STOP_CHARGING = 0
    START_CHARGING = 1


class EvCharger(AlphaEssModel):
    """EV charger registered at a system (getEvChargerConfigList).

    Attributes:
        evcharger_sn: Serial number of the EV charger.
        evcharger_model: Model of the EV charger.
    """

    evcharger_sn: str
    evcharger_model: str | None = None


class EvChargerCurrent(AlphaEssModel):
    """Household current limit for EV charging (getEvChargerCurrentsBySn).

    Attributes:
        currentsetting: Household current limit in A.
    """

    currentsetting: float | None = None


class EvChargerStatus(AlphaEssModel):
    """Charging state of an EV charger (getEvChargerStatusBySn).

    Attributes:
        evcharger_status: Current state; unknown codes are kept as plain int.
    """

    evcharger_status: EvChargerState | int = Field(union_mode="left_to_right")

"""Models describing the registered systems and their summary figures."""

from pydantic import AliasChoices, Field

from alphaessaio.models._base import AlphaEssModel


class EssSystem(AlphaEssModel):
    """System bound to the developer account (getEssList).

    Attributes:
        sys_sn: System serial number.
        cobat: Battery capacity in kWh.
        surplus_cobat: Remaining battery capacity in kWh.
        us_capacity: Usable battery capacity in percent.
        mbat: Battery model.
        minv: Inverter model.
        poinv: Nominal inverter power in kW.
        popv: Nominal PV power in kWp.
        ems_status: EMS status as reported by the cloud.
    """

    sys_sn: str
    cobat: float | None = Field(
        default=None, validation_alias=AliasChoices("cobat", "cbat")
    )
    surplus_cobat: float | None = None
    us_capacity: float | None = None
    mbat: str | None = None
    minv: str | None = None
    poinv: float | None = None
    popv: float | None = None
    ems_status: str | None = None


class SystemSummary(AlphaEssModel):
    """Aggregated energy and income figures of a system (getSumDataForCustomer).

    Attributes:
        epvtoday: PV generation today in kWh.
        epvtotal: Total PV generation in kWh.
        eload: Load consumption today in kWh.
        eoutput: Grid feed-in today in kWh.
        einput: Grid consumption today in kWh.
        echarge: Battery charge today in kWh.
        edischarge: Battery discharge today in kWh.
        today_income: Income today in `money_type`.
        total_income: Total income in `money_type`.
        eself_consumption: Self-consumption rate as fraction between 0 and 1,
            although the API documentation states percent.
        eself_sufficiency: Self-sufficiency rate as fraction between 0 and 1,
            although the API documentation states percent.
        tree_num: Equivalent number of trees planted.
        carbon_num: CO2 reduction in kg.
        money_type: Currency of the income figures.
    """

    epvtoday: float | None = None
    epvtotal: float | None = None
    eload: float | None = None
    eoutput: float | None = None
    einput: float | None = None
    echarge: float | None = None
    edischarge: float | None = None
    today_income: float | None = None
    total_income: float | None = None
    eself_consumption: float | None = None
    eself_sufficiency: float | None = None
    tree_num: float | None = None
    carbon_num: float | None = None
    money_type: str | None = None

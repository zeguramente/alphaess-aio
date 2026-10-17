"""Record real API responses as anonymised test fixtures.

Calls only read-only GET endpoints, parses every response with the library
models and writes the raw body to tests/fixtures/<endpoint>.json with the
system and EV charger serial numbers replaced by placeholders.

Usage::

    ALPHAESS_APPID=... ALPHAESS_APPSECRET=... ALPHAESS_SYSSN=... \\
        uv run python scripts/record_fixtures.py

Set ALPHAESS_EVCHARGER_SN as well to record the EV charger status endpoint.
"""

import asyncio
import datetime
import json
import logging
import os
from pathlib import Path

import aiohttp
from pydantic import TypeAdapter, ValidationError

from alphaessaio import AlphaEssAuth
from alphaessaio.models import (
    ChargeConfig,
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
from alphaessaio.transport import BASE_URL

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
_PLACEHOLDER_SYS_SN = "AL0000000000000"
_PLACEHOLDER_EVCHARGER_SN = "EV0000000000000"


def _build_requests(
    sys_sn: str, evcharger_sn: str | None
) -> list[tuple[str, dict[str, str], TypeAdapter]]:
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    by_sn = {"sysSn": sys_sn}
    by_sn_and_day = {"sysSn": sys_sn, "queryDate": yesterday}
    requests = [
        ("getEssList", {}, TypeAdapter(list[EssSystem])),
        ("getLastPowerData", by_sn, TypeAdapter(LastPowerData)),
        ("getOneDayPowerBySn", by_sn_and_day, TypeAdapter(list[PowerSample])),
        ("getOneDateEnergyBySn", by_sn_and_day, TypeAdapter(DailyEnergy)),
        ("getSumDataForCustomer", by_sn, TypeAdapter(SystemSummary)),
        ("getChargeConfigInfo", by_sn, TypeAdapter(ChargeConfig)),
        ("getDisChargeConfigInfo", by_sn, TypeAdapter(DischargeConfig)),
        ("getEvChargerConfigList", by_sn, TypeAdapter(list[EvCharger])),
        ("getEvChargerCurrentsBySn", by_sn, TypeAdapter(EvChargerCurrent)),
    ]
    if evcharger_sn:
        requests.append(
            (
                "getEvChargerStatusBySn",
                {"sysSn": sys_sn, "evchargerSn": evcharger_sn},
                TypeAdapter(list[EvChargerStatus]),
            )
        )
    return requests


def _anonymise(raw_body: str, sys_sn: str, evcharger_sn: str | None) -> str:
    anonymised = raw_body.replace(sys_sn, _PLACEHOLDER_SYS_SN)
    if evcharger_sn:
        anonymised = anonymised.replace(evcharger_sn, _PLACEHOLDER_EVCHARGER_SN)
    return anonymised


async def record_fixtures() -> None:
    """Fetch every read-only endpoint and store its anonymised response."""
    auth = AlphaEssAuth(
        appid=os.environ["ALPHAESS_APPID"],
        appsecret=os.environ["ALPHAESS_APPSECRET"],
    )
    sys_sn = os.environ["ALPHAESS_SYSSN"]
    evcharger_sn = os.environ.get("ALPHAESS_EVCHARGER_SN")

    async with aiohttp.ClientSession() as session:
        for endpoint, params, model in _build_requests(sys_sn, evcharger_sn):
            async with session.get(
                f"{BASE_URL}{endpoint}", params=params, headers=auth.create_headers()
            ) as response:
                raw_body = await response.text()
            body = json.loads(raw_body)
            if body.get("code") != 200:
                print(f"SKIP  {endpoint}: {body.get('code')} {body.get('msg')}")
                continue
            try:
                parsed = model.validate_python(body["data"])
            except ValidationError as err:
                print(f"FAIL  {endpoint}: does not match model\n{err}")
            else:
                print(f"OK    {endpoint}: {parsed!r:.100}")
            anonymised = json.loads(_anonymise(raw_body, sys_sn, evcharger_sn))
            (_FIXTURES_DIR / f"{endpoint}.json").write_text(
                json.dumps(anonymised, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            # Space out the calls to stay clear of server-side rate limiting.
            await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG if os.environ.get("DEBUG") else None)
    asyncio.run(record_fixtures())

# alphaess-aio – async client for the AlphaESS Open API

## About

Async (aiohttp) client for the [AlphaESS Open API](https://open.alphaess.com/).
It reads live power, daily energy and system data of your AlphaESS system and
changes battery charge/discharge windows and EV charger settings. All
responses are parsed into typed pydantic models.

## Prerequisites

Register at https://open.alphaess.com/ and bind your system. You receive an
AppID and AppSecret needed for authentication.

## How to use

```python
import asyncio
import datetime

from alphaessaio import AlphaEssAPI, AlphaEssAuth


async def main() -> None:
    auth = AlphaEssAuth(appid="your_app_id", appsecret="your_app_secret")

    async with AlphaEssAPI(auth) as api:
        for system in await api.get_ess_list():
            power = await api.get_last_power_data(system.sys_sn)
            print(system.sys_sn, power.ppv, power.soc)

            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            energy = await api.get_one_date_energy_by_sn(system.sys_sn, yesterday)
            print(energy.epv)


asyncio.run(main())
```

### Home Assistant

Pass Home Assistant's shared session; the client will not close it:

```python
from homeassistant.helpers.aiohttp_client import async_get_clientsession

api = AlphaEssAPI(auth, session=async_get_clientsession(hass))
```

### Changing settings

Read the current settings, change what you need and send them back.
Times must be on the 15 minute grid (00:00–23:45). AlphaESS accepts changes
only about once per day.

```python
config = await api.get_charge_config_info(sys_sn)
await api.update_charge_config_info(
    sys_sn,
    config.model_copy(update={"grid_charge": True, "bat_high_cap": 90}),
)
```

### Errors

All errors derive from `AlphaEssError`:

| Exception | Raised when |
|---|---|
| `AlphaEssAuthError` | AppID/AppSecret were rejected (code 6007) |
| `AlphaEssRequestError` | the API returned an error code (`.code`, `.message`) or invalid data |
| `AlphaEssConnectionError` | network error or timeout (default 30 s, `timeout=` to change) |

## Migrating from 0.2

- Methods return the payload model directly (e.g. `LastPowerData`,
  `list[EssSystem]`) instead of a wrapper with `code`/`info`/`data`.
  Setters, bind and unbind return `None`.
- `query_date` is a `datetime.date`, and `sys_sn` is now the first argument of
  `get_one_day_power_by_sn` / `get_one_date_energy_by_sn`.
- `update_charge_config_info` / `update_dis_charge_config_info` take a
  `ChargeConfig` / `DischargeConfig`; `remote_control_ev_charger` takes a
  `ControlMode`.
- `alphaessaio.response` was replaced by `alphaessaio.models`.

## Development

```bash
uv run --extra test --extra lint ruff check .
uv run --extra test pytest
```

Tests run against a local fake of the AlphaESS cloud using the JSON responses
in `tests/fixtures/`. To refresh them from your own system (read-only GET
endpoints only, serial numbers are anonymised):

```bash
ALPHAESS_APPID=... ALPHAESS_APPSECRET=... ALPHAESS_SYSSN=... \
    uv run python scripts/record_fixtures.py
```

"""Shared constants and loaders for the test suite."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Example credentials and serial numbers used in the AlphaESS documentation / fixtures.
DOC_APP_ID = "alphaef7900ee81dbbce9"
DOC_APP_SECRET = "c2d2ef6c047c49678e2c332fb2d74c3c"
FIXTURE_SYS_SN = "AL0000000000000"
FIXTURE_EVCHARGER_SN = "EV0000000000000"


def load_response(endpoint: str) -> dict:
    """Load a recorded response body from tests/fixtures/<endpoint>.json."""
    return json.loads((FIXTURES_DIR / f"{endpoint}.json").read_text(encoding="utf-8"))

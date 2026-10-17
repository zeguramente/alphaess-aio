"""Request signing for the AlphaESS Open API."""

import hashlib
import time

import pydantic


class AlphaEssAuth(pydantic.BaseModel):
    """Credentials of an AlphaESS developer account (https://open.alphaess.com).

    Attributes:
        appid: Developer ID (AppID).
        appsecret: Developer secret (AppSecret).
    """

    appid: str
    appsecret: pydantic.SecretStr

    def _get_signature(self, timestamp: str) -> str:
        return hashlib.sha512(
            f"{self.appid}{self.appsecret.get_secret_value()}{timestamp}".encode(
                "ascii"
            )
        ).hexdigest()

    def create_headers(self) -> dict[str, str]:
        """Create the signed authentication headers for one request.

        The signature is only valid for 300 seconds, so call this per request.

        Returns:
            Headers containing appId, timeStamp and sign.
        """
        timestamp = str(int(time.time()))
        return {
            "appId": self.appid,
            "timeStamp": timestamp,
            "sign": self._get_signature(timestamp),
        }

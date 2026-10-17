"""Exceptions raised by the AlphaESS client."""


class AlphaEssError(Exception):
    """Base class for all errors raised by this library."""


class AlphaEssConnectionError(AlphaEssError):
    """The AlphaESS cloud could not be reached or did not answer in time."""


class AlphaEssRequestError(AlphaEssError):
    """The AlphaESS cloud rejected the request or returned unusable data.

    Attributes:
        code: Return code of the API, or None if the response had none.
        message: Return message of the API or a description of the problem.
    """

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(f"{message} (code={code})")
        self.code = code
        self.message = message


class AlphaEssAuthError(AlphaEssRequestError):
    """The AppID / AppSecret combination was rejected."""

"""Common base for all AlphaESS response and request models."""

import logging

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel

_LOGGER = logging.getLogger(__name__)


class AlphaEssModel(BaseModel):
    """Base model mapping snake_case attributes to the camelCase API fields.

    Unknown fields are kept instead of rejected, so a new field added by
    AlphaESS does not break existing installations.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    @model_validator(mode="after")
    def _log_unknown_fields(self):
        if self.model_extra:
            _LOGGER.debug(
                "%s received unknown fields: %s",
                type(self).__name__,
                self.model_extra,
            )
        return self

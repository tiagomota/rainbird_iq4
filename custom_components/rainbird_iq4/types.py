"""Runtime data types for the RainBird IQ4 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pyiq4 import RainbirdIQ4Client

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import RainbirdIQ4Coordinator


@dataclass
class RainbirdIQ4Data:
    """Runtime data stored in config entry."""

    client: RainbirdIQ4Client
    coordinator: RainbirdIQ4Coordinator


type RainbirdIQ4ConfigEntry = ConfigEntry[RainbirdIQ4Data]

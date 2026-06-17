"""Data model for forge url."""

from dataclasses import dataclass


@dataclass()
class ForgeUrl:
    """Data model for forge url."""

    sshUrl: str
    url: str

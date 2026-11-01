from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for schemas that read directly off ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class Money(BaseModel):
    """Convenience wrapper so API responses carry a display-ready amount
    alongside the exact minor-unit integer, without ever doing float math."""

    minor_units: int
    currency: str

    @property
    def display(self) -> str:
        # Simple 2-decimal display; good enough for the currencies in demo
        # data (USD/EUR/TRY). A real multi-currency product would look up
        # each currency's minor-unit exponent instead of assuming 2.
        major = self.minor_units / 100
        return f"{major:.2f} {self.currency}"

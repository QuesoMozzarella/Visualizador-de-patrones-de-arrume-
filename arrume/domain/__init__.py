"""Nucleo del dominio: modelos y errores. No depende de plotly ni de la CLI."""

from .errors import ArrumeError, CajaNoCabe, ConfiguracionInvalida
from .models import Area, Arrume, Caja, Colocacion, Pallet, Pieza, Restricciones

__all__ = [
    "Area",
    "Arrume",
    "ArrumeError",
    "Caja",
    "CajaNoCabe",
    "Colocacion",
    "ConfiguracionInvalida",
    "Pallet",
    "Pieza",
    "Restricciones",
]

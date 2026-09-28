"""Nucleo del dominio: modelos y errores. No depende de Flask ni de la base de datos."""

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

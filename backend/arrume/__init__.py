"""Calculo de arrumes (pallet loading): el nucleo, sin web ni base de datos."""

from .domain import (
    Area,
    Arrume,
    ArrumeError,
    Caja,
    CajaNoCabe,
    Colocacion,
    ConfiguracionInvalida,
    Pallet,
    Pieza,
    Restricciones,
)
from .reporting import Informe, formatear, generar_informe
from .stacking import construir_por_pisos

__version__ = "0.1.0"

__all__ = [
    "Area",
    "Arrume",
    "ArrumeError",
    "Caja",
    "CajaNoCabe",
    "Colocacion",
    "ConfiguracionInvalida",
    "Informe",
    "Pallet",
    "Pieza",
    "Restricciones",
    "construir_por_pisos",
    "formatear",
    "generar_informe",
]

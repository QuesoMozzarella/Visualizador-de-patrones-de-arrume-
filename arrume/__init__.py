"""Generador y visualizador 3D de patrones de arrume (pallet loading)."""

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
from .stacking import construir_arrume

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
    "construir_arrume",
    "formatear",
    "generar_informe",
]

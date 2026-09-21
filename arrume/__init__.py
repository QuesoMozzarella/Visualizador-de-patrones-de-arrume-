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
from .trabazon import MejorAlterno, Rotacion180, SinTrabazon, Trabazon

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
    "MejorAlterno",
    "Pallet",
    "Pieza",
    "Restricciones",
    "Rotacion180",
    "SinTrabazon",
    "Trabazon",
    "construir_arrume",
    "formatear",
    "generar_informe",
]

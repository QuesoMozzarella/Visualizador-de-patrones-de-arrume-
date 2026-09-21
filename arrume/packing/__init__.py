"""Estrategias de patron de acomodo por nivel."""

from .base import EstrategiaPatron, centrar
from .guillotina import Guillotina

__all__ = ["EstrategiaPatron", "Guillotina", "centrar"]

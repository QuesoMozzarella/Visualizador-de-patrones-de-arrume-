"""Contrato que cumple toda estrategia de patron y utilidades compartidas.

Una estrategia recibe el area disponible y la base de la caja, y devuelve las
piezas de UN nivel. El contrato que debe respetar (verificado en los tests
para todas las estrategias por igual):

  - ninguna pieza se sale del area,
  - ningun par de piezas se solapa,
  - cada pieza mide exactamente la caja, en una de sus dos orientaciones.
"""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from ..domain.models import Area, Pieza


@runtime_checkable
class EstrategiaPatron(Protocol):
    """Genera el patron de acomodo de un nivel."""

    nombre: str

    def generar(self, area: Area, caja: Area) -> List[Pieza]:
        """Devuelve las piezas de un nivel, o una lista vacia si no cabe ninguna."""
        ...


def centrar(piezas: List[Pieza], area: Area) -> List[Pieza]:
    """Desplaza el patron para que quede centrado sobre el area."""
    if not piezas:
        return []
    usado_x = max(pieza.x2 for pieza in piezas)
    usado_y = max(pieza.y2 for pieza in piezas)
    ox = (area.ancho - usado_x) / 2
    oy = (area.profundidad - usado_y) / 2
    return [
        Pieza(pieza.x + ox, pieza.y + oy, pieza.ancho, pieza.profundidad)
        for pieza in piezas
    ]

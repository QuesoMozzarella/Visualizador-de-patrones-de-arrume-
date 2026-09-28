"""Comprobaciones que todo patron y todo arrume deben cumplir.

Las de dos dimensiones viven en el paquete (arrume.packing.validacion),
porque el programa tambien las necesita para validar un nivel acomodado a
mano. Aqui solo se les pone el nombre con el que hablan los tests, y se
anade la de tres dimensiones, que es cosa de los tests.
"""

from __future__ import annotations

from itertools import combinations

from arrume.packing.validacion import (
    TOL,
    fuera_del_area,
    mide_la_caja,
    pares_que_se_solapan,
)

__all__ = [
    "TOL",
    "fuera_del_area",
    "mide_la_caja",
    "sin_solapamientos_2d",
    "sin_solapamientos_3d",
]


def sin_solapamientos_2d(piezas) -> list:
    """Devuelve los pares de piezas que se pisan (vacio si el patron es valido)."""
    return pares_que_se_solapan(piezas)


def sin_solapamientos_3d(cajas) -> list:
    """Pares de colocaciones que ocupan el mismo volumen."""
    def pisan(a1, a2, b1, b2):
        return min(a2, b2) - max(a1, b1) > TOL

    return [
        (p, q)
        for p, q in combinations(cajas, 2)
        if pisan(p.x, p.x2, q.x, q.x2)
        and pisan(p.y, p.y2, q.y, q.y2)
        and pisan(p.z, p.z2, q.z, q.z2)
    ]

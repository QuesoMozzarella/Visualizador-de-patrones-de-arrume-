"""Cuando un acomodo de nivel sirve, y por que no sirve.

Son las mismas comprobaciones que los tests le exigen a toda estrategia,
puestas donde el programa tambien pueda usarlas: al acomodar un nivel a
mano hay que poder decir que esta mal y senalar la caja culpable.

Las funciones devuelven indices, no piezas, para que la interfaz pueda
marcar exactamente cual falla.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations

from ..domain.models import Area, Numero, Pieza

TOL = 1e-6


def _se_pisan(a1: Numero, a2: Numero, b1: Numero, b2: Numero) -> bool:
    """True si los intervalos [a1,a2) y [b1,b2) comparten mas que la tolerancia."""
    return min(a2, b2) - max(a1, b1) > TOL


def pares_que_se_solapan(piezas: Sequence[Pieza]) -> list[tuple[int, int]]:
    """Parejas de cajas que ocupan el mismo sitio."""
    return [
        (i, j)
        for (i, p), (j, q) in combinations(enumerate(piezas), 2)
        if _se_pisan(p.x, p.x2, q.x, q.x2) and _se_pisan(p.y, p.y2, q.y, q.y2)
    ]


def fuera_del_area(piezas: Sequence[Pieza], area: Area) -> list[int]:
    """Cajas que se salen de la superficie disponible."""
    return [
        i
        for i, p in enumerate(piezas)
        if p.x < -TOL
        or p.y < -TOL
        or p.x2 > area.ancho + TOL
        or p.y2 > area.profundidad + TOL
    ]


def mide_la_caja(pieza: Pieza, caja: Area) -> bool:
    """La pieza debe ser la caja, en una de sus dos orientaciones sobre Z."""
    lados = sorted((pieza.ancho, pieza.profundidad))
    esperado = sorted((caja.ancho, caja.profundidad))
    return all(abs(a - b) < TOL for a, b in zip(lados, esperado, strict=True))


def no_miden_la_caja(piezas: Sequence[Pieza], caja: Area) -> list[int]:
    """Cajas con una medida que no es la de la caja del arrume."""
    return [i for i, p in enumerate(piezas) if not mide_la_caja(p, caja)]


def problemas(piezas: Sequence[Pieza], area: Area, caja: Area) -> list[str]:
    """Lo que impide usar este acomodo, en frases para leer.

    Lista vacia = el acomodo sirve.
    """
    if not piezas:
        return ["El nivel no tiene ninguna caja."]

    fallos = []

    salidas = fuera_del_area(piezas, area)
    if salidas:
        fallos.append(
            "{} {} de la superficie disponible.".format(
                _cuantas(salidas), "se sale" if len(salidas) == 1 else "se salen"
            )
        )

    choques = pares_que_se_solapan(piezas)
    if choques:
        fallos.append(
            "{} de cajas se {}.".format(
                "1 pareja" if len(choques) == 1 else f"{len(choques)} parejas",
                "pisa" if len(choques) == 1 else "pisan",
            )
        )

    ajenas = no_miden_la_caja(piezas, caja)
    if ajenas:
        fallos.append(
            f"{_cuantas(ajenas)} no mide {caja.ancho} x {caja.profundidad} cm."
        )

    return fallos


def _cuantas(indices: Sequence[int]) -> str:
    return "1 caja" if len(indices) == 1 else f"{len(indices)} cajas"

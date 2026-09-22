"""Comprobaciones que todo patron y todo arrume deben cumplir.

Se usan desde varios tests, por eso viven aparte: el contrato es uno solo,
independiente de la estrategia que genero el patron.
"""

from __future__ import annotations

from itertools import combinations

TOL = 1e-6


def _se_solapan(a1, a2, b1, b2) -> bool:
    """True si los intervalos [a1,a2) y [b1,b2) comparten mas que la tolerancia."""
    return min(a2, b2) - max(a1, b1) > TOL


def sin_solapamientos_2d(piezas) -> list:
    """Devuelve los pares de piezas que se pisan (vacio si el patron es valido)."""
    malos = []
    for p, q in combinations(piezas, 2):
        if _se_solapan(p.x, p.x2, q.x, q.x2) and _se_solapan(p.y, p.y2, q.y, q.y2):
            malos.append((p, q))
    return malos


def sin_solapamientos_3d(cajas) -> list:
    """Pares de colocaciones que ocupan el mismo volumen."""
    malos = []
    for p, q in combinations(cajas, 2):
        if (
            _se_solapan(p.x, p.x2, q.x, q.x2)
            and _se_solapan(p.y, p.y2, q.y, q.y2)
            and _se_solapan(p.z, p.z2, q.z, q.z2)
        ):
            malos.append((p, q))
    return malos


def fuera_del_area(piezas, area) -> list:
    """Piezas que se salen del area disponible."""
    return [
        p
        for p in piezas
        if p.x < -TOL
        or p.y < -TOL
        or p.x2 > area.ancho + TOL
        or p.y2 > area.profundidad + TOL
    ]


def mide_la_caja(pieza, caja) -> bool:
    """La pieza debe ser la caja, en una de sus dos orientaciones sobre Z."""
    lados = sorted((pieza.ancho, pieza.profundidad))
    esperado = sorted((caja.ancho, caja.profundidad))
    return all(abs(a - b) < TOL for a, b in zip(lados, esperado, strict=True))

"""Transformaciones rigidas de un patron dentro de su area.

Son funciones puras sobre listas de Pieza: reciben un patron valido y
devuelven otro patron valido (mismas cajas, mismas medidas, otra posicion).
Se usan para construir los candidatos a nivel alterno del trabado.
"""

from __future__ import annotations

from ..domain.models import Area, Numero, Pieza


def rotar_180(piezas: list[Pieza], area: Area) -> list[Pieza]:
    """Gira el patron completo media vuelta sobre el centro del area."""
    return [
        Pieza(area.ancho - p.x2, area.profundidad - p.y2, p.ancho, p.profundidad)
        for p in piezas
    ]


def espejo_x(piezas: list[Pieza], area: Area) -> list[Pieza]:
    """Refleja el patron sobre el eje vertical del area."""
    return [Pieza(area.ancho - p.x2, p.y, p.ancho, p.profundidad) for p in piezas]


def espejo_y(piezas: list[Pieza], area: Area) -> list[Pieza]:
    """Refleja el patron sobre el eje horizontal del area."""
    return [Pieza(p.x, area.profundidad - p.y2, p.ancho, p.profundidad) for p in piezas]


def holgura(piezas: list[Pieza], area: Area) -> tuple[Numero, Numero]:
    """Espacio libre que le sobra al patron en cada eje."""
    if not piezas:
        return (area.ancho, area.profundidad)
    usado_x = max(p.x2 for p in piezas) - min(p.x for p in piezas)
    usado_y = max(p.y2 for p in piezas) - min(p.y for p in piezas)
    return (area.ancho - usado_x, area.profundidad - usado_y)


def desplazar(piezas: list[Pieza], dx: Numero, dy: Numero) -> list[Pieza]:
    """Mueve el patron completo sin deformarlo."""
    return [Pieza(p.x + dx, p.y + dy, p.ancho, p.profundidad) for p in piezas]


def a_esquina(
    piezas: list[Pieza], area: Area, signo_x: int, signo_y: int
) -> list[Pieza]:
    """Arrima el patron a una esquina aprovechando toda la holgura.

    El patron viene centrado, asi que la mitad de la holgura esta a cada
    lado: correrlo esa mitad lo pega al borde sin sacarlo del area.
    """
    hx, hy = holgura(piezas, area)
    return desplazar(piezas, signo_x * hx / 2, signo_y * hy / 2)

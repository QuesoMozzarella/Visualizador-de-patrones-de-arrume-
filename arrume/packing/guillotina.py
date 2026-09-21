"""Empaquetado 2D por cortes guillotina con memoizacion.

Es el motor original del proyecto, extraido tal cual: prueba bloques
uniformes en las dos orientaciones de la caja y todos los cortes guillotina
horizontales y verticales, quedandose con el que mas cajas mete.

La unica diferencia con el original es que ahora tolera medidas decimales:
las posiciones se redondean a _DECIMALES para que el ruido de coma flotante
no multiplique las claves de la memoizacion ni pierda una caja por 1e-15 cm.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..domain.models import Area, Numero, Pieza
from .base import centrar

_DECIMALES = 6

_Rect = Tuple[Numero, Numero, Numero, Numero]


def _r(valor: Numero) -> Numero:
    """Redondea para que 39.999999999 y 40 sean la misma medida."""
    return round(valor, _DECIMALES)


def _cuantas(total: Numero, paso: Numero) -> int:
    """Cuantas veces cabe 'paso' en 'total' (division entera tolerante)."""
    return int(round(total / paso, _DECIMALES))


def _cortes(limite: Numero, a: Numero, b: Numero) -> List[Numero]:
    """Posiciones de corte utiles: todo i*a + j*b que quepa en 'limite'."""
    vals = set()
    i = 0
    while i * a <= limite:
        j = 0
        while i * a + j * b <= limite:
            vals.add(_r(i * a + j * b))
            j += 1
        i += 1
    return sorted(v for v in vals if 0 < v < limite)


def _mejor(
    ancho: Numero,
    profundidad: Numero,
    a: Numero,
    b: Numero,
    memo: Dict[Tuple[Numero, Numero], List[_Rect]],
) -> List[_Rect]:
    """Mejor acomodo de cajas a*b dentro de un rectangulo ancho*profundidad."""
    clave = (_r(ancho), _r(profundidad))
    if clave in memo:
        return memo[clave]

    mejor: List[_Rect] = []

    # Opcion A: un bloque uniforme, en cada una de las dos orientaciones
    for dx, dy in ((a, b), (b, a)):
        nx, ny = _cuantas(ancho, dx), _cuantas(profundidad, dy)
        if nx and ny and nx * ny > len(mejor):
            mejor = [
                (ix * dx, iy * dy, dx, dy) for ix in range(nx) for iy in range(ny)
            ]

    # Opcion B: partir en dos por X y resolver cada mitad
    for x in _cortes(ancho, a, b):
        if 2 * x > ancho:
            break
        izq = _mejor(x, profundidad, a, b, memo)
        der = _mejor(ancho - x, profundidad, a, b, memo)
        if len(izq) + len(der) > len(mejor):
            mejor = izq + [(px + x, py, pdx, pdy) for px, py, pdx, pdy in der]

    # Opcion C: partir en dos por Y
    for y in _cortes(profundidad, a, b):
        if 2 * y > profundidad:
            break
        aba = _mejor(ancho, y, a, b, memo)
        arr = _mejor(ancho, profundidad - y, a, b, memo)
        if len(aba) + len(arr) > len(mejor):
            mejor = aba + [(px, py + y, pdx, pdy) for px, py, pdx, pdy in arr]

    memo[clave] = mejor
    return mejor


class Guillotina:
    """Estrategia de patron por cortes guillotina."""

    nombre = "guillotina"

    def generar(self, area: Area, caja: Area) -> List[Pieza]:
        crudo = _mejor(area.ancho, area.profundidad, caja.ancho, caja.profundidad, {})
        if not crudo:
            return []
        piezas = [Pieza(x, y, dx, dy) for x, y, dx, dy in crudo]
        return centrar(piezas, area)

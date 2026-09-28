"""Empaquetado 2D por cortes guillotina con memoizacion.

Es el motor original del proyecto, extraido tal cual: prueba bloques
uniformes en las dos orientaciones de la caja y todos los cortes guillotina
horizontales y verticales, quedandose con el que mas cajas mete.

La unica diferencia con el original es que ahora tolera medidas decimales:
las posiciones se redondean a _DECIMALES para que el ruido de coma flotante
no multiplique las claves de la memoizacion ni pierda una caja por 1e-15 cm.
"""

from __future__ import annotations

from ..domain.models import Area, Numero, Pieza
from .base import centrar

_DECIMALES = 6

_Rect = tuple[Numero, Numero, Numero, Numero]


def _r(valor: Numero) -> Numero:
    """Redondea para que 39.999999999 y 40 sean la misma medida."""
    return round(valor, _DECIMALES)


def _cuantas(total: Numero, paso: Numero) -> int:
    """Cuantas veces cabe 'paso' en 'total' (division entera tolerante)."""
    return int(round(total / paso, _DECIMALES))


def _cortes(limite: Numero, a: Numero, b: Numero) -> list[Numero]:
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
    memo: dict[tuple[Numero, Numero], list[_Rect]],
) -> list[_Rect]:
    """Mejor acomodo de cajas a*b dentro de un rectangulo ancho*profundidad."""
    clave = (_r(ancho), _r(profundidad))
    if clave in memo:
        return memo[clave]

    mejor: list[_Rect] = []

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


def _bloque(
    ancho: Numero, profundidad: Numero, a: Numero, b: Numero
) -> list[_Rect]:
    """El mejor bloque uniforme (todas iguales) en un rectangulo."""
    mejor: list[_Rect] = []
    for dx, dy in ((a, b), (b, a)):
        nx, ny = _cuantas(ancho, dx), _cuantas(profundidad, dy)
        if nx * ny > len(mejor):
            mejor = [
                (ix * dx, iy * dy, dx, dy) for ix in range(nx) for iy in range(ny)
            ]
    return mejor


def _rapido(ancho: Numero, profundidad: Numero, a: Numero, b: Numero) -> list[_Rect]:
    """Dos bloques uniformes, uno al lado del otro: el mejor corte unico.

    Es lo que usan los programas de paletizado con cajas chicas, donde el
    calculo exacto se dispara. Pierde poco: con muchas cajas por nivel, una
    fila de mas o de menos pesa poco en el total.
    """
    mejor = _bloque(ancho, profundidad, a, b)
    for x in _cortes(ancho, a, b):
        izq = _bloque(x, profundidad, a, b)
        der = _bloque(ancho - x, profundidad, a, b)
        if len(izq) + len(der) > len(mejor):
            mejor = izq + [(px + x, py, pdx, pdy) for px, py, pdx, pdy in der]
    for y in _cortes(profundidad, a, b):
        aba = _bloque(ancho, y, a, b)
        arr = _bloque(ancho, profundidad - y, a, b)
        if len(aba) + len(arr) > len(mejor):
            mejor = aba + [(px, py + y, pdx, pdy) for px, py, pdx, pdy in arr]
    return mejor


# Por encima de estas combinaciones de corte (posibles en X por posibles en
# Y) el calculo exacto pasa de medio segundo y se usa el rapido
COMPLEJIDAD_MAXIMA = 3000


class Guillotina:
    """Estrategia de patron por cortes guillotina."""

    nombre = "guillotina"

    def generar(self, area: Area, caja: Area) -> list[Pieza]:
        a, b = caja.ancho, caja.profundidad
        cortes = len(_cortes(area.ancho, a, b)) * len(_cortes(area.profundidad, a, b))
        if cortes > COMPLEJIDAD_MAXIMA:
            crudo = _rapido(area.ancho, area.profundidad, a, b)
        else:
            crudo = _mejor(area.ancho, area.profundidad, a, b, {})
        if not crudo:
            return []
        piezas = [Pieza(x, y, dx, dy) for x, y, dx, dy in crudo]
        return centrar(piezas, area)

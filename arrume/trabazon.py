"""Trabazon: como se alterna el patron entre un nivel y el siguiente.

Un arrume traba cuando las cajas de un nivel pisan las juntas del nivel de
abajo, en vez de apoyarse cada una sobre una sola caja (lo que forma
columnas independientes y deja el arrume suelto).

Aqui viven la medida de la trabazon y las estrategias para conseguirla.
Estan separadas del empaquetado porque son decisiones distintas: una elige
como llenar UN nivel, la otra como encadenar DOS.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from typing import Protocol, runtime_checkable

from .domain.models import Area, Numero, Pieza
from .packing.base import EstrategiaPatron
from .packing.transformaciones import a_esquina, espejo_x, espejo_y, rotar_180

_TOL = 1e-6


# =====================================================================
# Medida
# =====================================================================


def _solape(a: Pieza, b: Pieza) -> Numero:
    """Superficie compartida por dos piezas."""
    ancho = min(a.x2, b.x2) - max(a.x, b.x)
    profundidad = min(a.y2, b.y2) - max(a.y, b.y)
    if ancho <= 0 or profundidad <= 0:
        return 0
    return ancho * profundidad


def _apoyo_maximo(pieza: Pieza, nivel: Sequence[Pieza]) -> float:
    """Que fraccion de la pieza se apoya sobre una sola caja de abajo.

    1.0 = la caja esta calcada sobre la de abajo (no traba nada).
    0.5 = reparte su apoyo entre dos cajas (traba bien).
    """
    if not nivel:
        return 0.0
    return max(_solape(pieza, otra) for otra in nivel) / pieza.superficie


def cajas_calcadas(inferior: Sequence[Pieza], superior: Sequence[Pieza]) -> int:
    """Cuantas cajas del nivel de arriba caen justo sobre una de abajo."""
    return sum(1 for p in superior if _apoyo_maximo(p, inferior) >= 1 - _TOL)


def calidad(inferior: Sequence[Pieza], superior: Sequence[Pieza]) -> float:
    """Trabazon de 0 a 1: cuanto reparten su apoyo las cajas de arriba.

    0 = todas calcadas (no traba). Los valores altos indican que cada caja
    se apoya sobre varias de abajo, que es justo lo que amarra el arrume.
    """
    if not superior:
        return 0.0
    promedio = sum(_apoyo_maximo(p, inferior) for p in superior) / len(superior)
    return 1.0 - promedio


# =====================================================================
# Estrategias
# =====================================================================


@runtime_checkable
class Trabazon(Protocol):
    """Decide el patron de los niveles impares a partir del patron base."""

    nombre: str

    def alterno(
        self,
        base: Sequence[Pieza],
        area: Area,
        caja: Area,
        estrategia: EstrategiaPatron,
    ) -> list[Pieza]:
        ...


class SinTrabazon:
    """Arrume en columna: todos los niveles iguales."""

    nombre = "en columna"

    def alterno(
        self,
        base: Sequence[Pieza],
        area: Area,
        caja: Area,
        estrategia: EstrategiaPatron,
    ) -> list[Pieza]:
        return list(base)


class Rotacion180:
    """Gira el nivel media vuelta.

    Es lo que hacia el proyecto originalmente. Se conserva para poder
    compararlo, pero no traba cuando el patron base es simetrico: medido
    sobre 10 configuraciones habituales, solo trabo en 3.
    """

    nombre = "rotacion 180"

    def alterno(
        self,
        base: Sequence[Pieza],
        area: Area,
        caja: Area,
        estrategia: EstrategiaPatron,
    ) -> list[Pieza]:
        return rotar_180(list(base), area)


class MejorAlterno:
    """Prueba varios patrones alternos y se queda con el que mas traba.

    Candidatos, todos con la misma cantidad de cajas que el patron base:
    giro de media vuelta, los dos espejos, el patron arrimado a cada
    esquina (aprovecha la holgura que el centrado reparte) y el patron que
    sale de preferir la caja girada.

    Si el nivel llena el area de forma exacta no hay ningun movimiento
    posible y se devuelve el patron base: el arrume no traba y el informe
    lo dice, en vez de aparentar una trabazon que no existe.
    """

    nombre = "mejor alterno"

    def alterno(
        self,
        base: Sequence[Pieza],
        area: Area,
        caja: Area,
        estrategia: EstrategiaPatron,
    ) -> list[Pieza]:
        piezas = list(base)
        mejor = piezas
        mejor_calidad = 0.0

        for candidato in self._candidatos(piezas, area, caja, estrategia):
            if len(candidato) != len(piezas):
                continue
            puntaje = calidad(piezas, candidato)
            if puntaje > mejor_calidad + _TOL:
                mejor, mejor_calidad = candidato, puntaje

        return mejor

    def _candidatos(
        self,
        base: list[Pieza],
        area: Area,
        caja: Area,
        estrategia: EstrategiaPatron,
    ) -> Iterator[list[Pieza]]:
        """En orden: cuanto mas arriba, mas se prefiere ante un empate."""
        yield rotar_180(base, area)
        yield espejo_x(base, area)
        yield espejo_y(base, area)
        for signo_x, signo_y in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            yield a_esquina(base, area, signo_x, signo_y)

        # Preferir la caja girada suele dar otro acomodo con las mismas cajas
        girado = estrategia.generar(area, Area(caja.profundidad, caja.ancho))
        if girado:
            yield girado
            yield rotar_180(girado, area)
            for signo_x, signo_y in ((1, 1), (-1, -1)):
                yield a_esquina(girado, area, signo_x, signo_y)


# Trabazones que se pueden elegir por nombre desde la CLI o la interfaz
TRABAZONES: dict[str, Callable[[], Trabazon]] = {
    "mejor": MejorAlterno,
    "rotacion": Rotacion180,
}


def elegir(trabado: bool, trabazon: Trabazon | None = None) -> Trabazon:
    """Trabazon a usar segun las restricciones."""
    if not trabado:
        return SinTrabazon()
    return trabazon if trabazon is not None else MejorAlterno()

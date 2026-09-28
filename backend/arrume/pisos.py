"""Pisos: cada nivel del arrume va normal o cruzado.

El acomodo de un nivel lo decide el usuario (o, si no dice nada, el motor
de empaquetado). Cada piso lleva ese acomodo tal cual -- normal -- o
girado media vuelta -- cruzado --, que es lo que se hace en bodega al
voltear el tendido de un piso al siguiente.
"""

from __future__ import annotations

from collections.abc import Sequence

from .domain.errors import ConfiguracionInvalida
from .domain.models import Area, Pieza
from .packing.transformaciones import rotar_180

NORMAL = "normal"
CRUZADO = "cruzado"
FORMAS = (NORMAL, CRUZADO)


def cruzar(piezas: Sequence[Pieza], area: Area) -> list[Pieza]:
    """El acomodo cruzado: el mismo, girado media vuelta sobre el pallet."""
    return rotar_180(list(piezas), area)


def reparto(niveles: int, cruzados: bool = True, iguales: int = 1) -> list[str]:
    """Si cada piso va normal o cruzado, de abajo arriba.

    Sin cruzar, todos van normales. Cruzando, los primeros 'iguales' van
    normales, el siguiente cruzado y de ahi en adelante se turnan:

        iguales=1  ->  N C N C N C
        iguales=2  ->  N N C N C N
    """
    if isinstance(iguales, bool) or not isinstance(iguales, int) or iguales < 1:
        raise ConfiguracionInvalida(
            f"Los primeros niveles iguales deben ser al menos 1 (recibido {iguales})."
        )
    if not cruzados:
        return [NORMAL] * niveles
    return [
        NORMAL if nivel < iguales or (nivel - iguales) % 2 == 1 else CRUZADO
        for nivel in range(niveles)
    ]


def validar(pisos: Sequence[str]) -> list[str]:
    """Los pisos tal cual, o un error que dice que se esperaba."""
    malos = [forma for forma in pisos if forma not in FORMAS]
    if malos:
        raise ConfiguracionInvalida(
            f"Cada piso va 'normal' o 'cruzado', no '{malos[0]}'."
        )
    return list(pisos)

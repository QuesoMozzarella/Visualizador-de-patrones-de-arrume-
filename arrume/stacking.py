"""Apilado: convierte el patron de un nivel en el arrume completo.

Capa pura: calcula y devuelve un Arrume, o lanza un error del dominio.
No imprime, no escribe archivos y no termina el proceso.
"""

from __future__ import annotations

from typing import List, Optional

from .domain.errors import CajaNoCabe
from .domain.models import Area, Arrume, Caja, Colocacion, Pallet, Pieza, Restricciones
from .packing.base import EstrategiaPatron
from .packing.guillotina import Guillotina


def area_disponible(pallet: Pallet, restricciones: Restricciones) -> Area:
    """Superficie utilizable: el pallet mas el vuelo permitido por lado."""
    return Area(
        pallet.ancho + 2 * restricciones.vuelo,
        pallet.profundidad + 2 * restricciones.vuelo,
    )


def construir_arrume(
    pallet: Pallet,
    caja: Caja,
    restricciones: Restricciones,
    estrategia: Optional[EstrategiaPatron] = None,
) -> Arrume:
    """Genera el arrume completo apilando el patron nivel a nivel."""
    if estrategia is None:
        estrategia = Guillotina()

    area = area_disponible(pallet, restricciones)
    base = tuple(estrategia.generar(area, caja.base))
    if not base:
        raise CajaNoCabe(
            "Ninguna caja de {} x {} cm cabe en un area de {} x {} cm.".format(
                caja.ancho, caja.profundidad, area.ancho, area.profundidad
            )
        )

    cajas: List[Colocacion] = []
    for nivel in range(restricciones.niveles):
        z = pallet.alto + nivel * caja.alto
        for pieza in _piezas_del_nivel(base, area, nivel, restricciones):
            cajas.append(
                Colocacion(
                    pieza.x - restricciones.vuelo,
                    pieza.y - restricciones.vuelo,
                    z,
                    pieza.ancho,
                    pieza.profundidad,
                    caja.alto,
                    nivel,
                )
            )

    return Arrume(
        pallet=pallet,
        caja=caja,
        restricciones=restricciones,
        patron_base=base,
        cajas=tuple(cajas),
        estrategia=estrategia.nombre,
    )


def _piezas_del_nivel(
    base: tuple, area: Area, nivel: int, restricciones: Restricciones
) -> List[Pieza]:
    """Patron de un nivel concreto, con la trabazon aplicada si toca.

    OJO: el trabado actual gira el nivel completo 180 grados. Si el patron
    base es simetrico respecto al centro -- que es lo normal, porque se
    centra sobre el area -- el nivel girado queda identico al original y no
    hay trabazon real. Pendiente de corregir con un patron alterno propio.
    """
    if not (restricciones.trabado and nivel % 2 == 1):
        return list(base)
    return [
        Pieza(
            area.ancho - pieza.x - pieza.ancho,
            area.profundidad - pieza.y - pieza.profundidad,
            pieza.ancho,
            pieza.profundidad,
        )
        for pieza in base
    ]

"""Apilado: convierte el patron de un nivel en el arrume completo.

Capa pura: calcula y devuelve un Arrume, o lanza un error del dominio.
No imprime, no escribe archivos y no termina el proceso.
"""

from __future__ import annotations

from collections.abc import Sequence

from .domain.errors import CajaNoCabe, ConfiguracionInvalida
from .domain.models import Area, Arrume, Caja, Colocacion, Pallet, Pieza, Restricciones
from .packing.base import EstrategiaPatron
from .packing.guillotina import Guillotina
from .trabazon import Trabazon, elegir


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
    estrategia: EstrategiaPatron | None = None,
    trabazon: Trabazon | None = None,
) -> Arrume:
    """Genera el arrume completo apilando los patrones nivel a nivel.

    'estrategia' decide como se llena un nivel; 'trabazon', como se alterna
    entre niveles. Las dos se pueden cambiar sin tocar este apilado.
    """
    if estrategia is None:
        estrategia = Guillotina()

    area = area_disponible(pallet, restricciones)
    base = tuple(estrategia.generar(area, caja.base))
    if not base:
        raise CajaNoCabe(
            f"Ninguna caja de {caja.ancho} x {caja.profundidad} cm cabe "
            f"en un area de {area.ancho} x {area.profundidad} cm."
        )

    modo = elegir(restricciones.trabado, trabazon)
    alterno = tuple(modo.alterno(base, area, caja.base, estrategia))
    if len(alterno) != len(base):
        raise ConfiguracionInvalida(
            f"La trabazon '{modo.nombre}' devolvio {len(alterno)} cajas "
            f"y el patron base tiene {len(base)}: "
            "todos los niveles deben llevar las mismas cajas."
        )

    cajas: list[Colocacion] = []
    for nivel in range(restricciones.niveles):
        z = pallet.alto + nivel * caja.alto
        patron = base if nivel % 2 == 0 else alterno
        cajas.extend(_colocar(patron, z, nivel, caja.alto, restricciones.vuelo))

    return Arrume(
        pallet=pallet,
        caja=caja,
        restricciones=restricciones,
        patron_base=base,
        cajas=tuple(cajas),
        estrategia=estrategia.nombre,
        patron_alterno=alterno,
        trabazon=modo.nombre,
    )


def _colocar(
    patron: Sequence[Pieza],
    z: float,
    nivel: int,
    alto: float,
    vuelo: float,
) -> list[Colocacion]:
    """Lleva un patron del sistema del area al del pallet, a la altura z."""
    return [
        Colocacion(
            pieza.x - vuelo,
            pieza.y - vuelo,
            z,
            pieza.ancho,
            pieza.profundidad,
            alto,
            nivel,
        )
        for pieza in patron
    ]

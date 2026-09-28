"""Apilado: de los acomodos de nivel al arrume completo.

Capa pura: calcula y devuelve un Arrume, o lanza un error del dominio.
No imprime, no escribe archivos y no termina el proceso.

Hay dos entradas, y la primera esta escrita sobre la segunda:

  construir_por_pisos     un acomodo de nivel, y cada piso normal o cruzado
  construir_con_acomodos  que acomodos hay y cual va en cada nivel
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from .domain.errors import AcomodoInvalido, CajaNoCabe, ConfiguracionInvalida
from .domain.models import (
    MAXIMO_CAJAS_POR_NIVEL,
    Acomodo,
    Area,
    Arrume,
    Caja,
    Colocacion,
    Pallet,
    Pieza,
    Restricciones,
)
from .packing.base import EstrategiaPatron
from .packing.guillotina import Guillotina
from .packing.validacion import problemas
from .pisos import CRUZADO, NORMAL, cruzar, validar


def area_disponible(pallet: Pallet, restricciones: Restricciones) -> Area:
    """Superficie utilizable: el pallet mas el vuelo permitido por lado."""
    return Area(
        pallet.ancho + 2 * restricciones.vuelo,
        pallet.profundidad + 2 * restricciones.vuelo,
    )


def construir_por_pisos(
    pallet: Pallet,
    caja: Caja,
    restricciones: Restricciones,
    pisos: Sequence[str],
    acomodo: Sequence[Pieza] | None = None,
    estrategia: EstrategiaPatron | None = None,
) -> Arrume:
    """Arrume con un acomodo de nivel y, por piso, si va normal o cruzado.

    'acomodo' son las cajas de un nivel en coordenadas del area disponible.
    Si no se da, lo calcula 'estrategia' (por defecto la guillotina, que
    mete el maximo de cajas).
    'pisos' dice, de abajo arriba, 'normal' o 'cruzado' para cada nivel.
    'trabado' queda en True cuando hay pisos de las dos formas.
    """
    pisos = validar(pisos)
    if len(pisos) != restricciones.niveles:
        raise ConfiguracionInvalida(
            f"Hay {len(pisos)} pisos indicados para {restricciones.niveles} niveles."
        )

    area = area_disponible(pallet, restricciones)
    motor = estrategia or Guillotina()
    if acomodo is not None:
        piezas = list(acomodo)
        if len(piezas) > MAXIMO_CAJAS_POR_NIVEL:
            raise ConfiguracionInvalida(
                f"Un nivel puede llevar hasta {MAXIMO_CAJAS_POR_NIVEL} cajas "
                f"(el acomodo trae {len(piezas)})."
            )
    else:
        # Se comprueba antes de calcular: con una caja diminuta (un "1" a
        # medio escribir) el motor tardaria minutos
        caben = int(area.superficie // caja.base.superficie)
        if caben > MAXIMO_CAJAS_POR_NIVEL:
            raise ConfiguracionInvalida(
                f"La caja es muy chica para este pallet: entrarian unas {caben} "
                f"por nivel y el maximo es {MAXIMO_CAJAS_POR_NIVEL}. "
                "Revisa las medidas."
            )
        piezas = motor.generar(area, caja.base)
        if not piezas:
            raise CajaNoCabe(
                f"La caja de {caja.ancho} x {caja.profundidad} cm no cabe "
                f"en el pallet de {pallet.ancho} x {pallet.profundidad} cm."
            )

    formas = {NORMAL: tuple(piezas), CRUZADO: tuple(cruzar(piezas, area))}
    usadas = [forma for forma in (NORMAL, CRUZADO) if forma in pisos]
    acomodos = [Acomodo(forma, formas[forma]) for forma in usadas]

    return construir_con_acomodos(
        pallet,
        caja,
        replace(restricciones, trabado=len(usadas) > 1),
        acomodos,
        [usadas.index(forma) for forma in pisos],
        estrategia=motor.nombre if acomodo is None else "a mano",
    )


def acomodo_normal(arrume: Arrume) -> tuple[Pieza, ...]:
    """El acomodo sin cruzar de un arrume hecho por pisos.

    Aunque ningun piso vaya normal se puede saber: media vuelta dos veces
    deja las cajas donde estaban, asi que basta con volver a cruzar.
    """
    for acomodo in arrume.acomodos:
        if acomodo.nombre == NORMAL:
            return acomodo.piezas
    area = area_disponible(arrume.pallet, arrume.restricciones)
    return tuple(cruzar(arrume.acomodos[0].piezas, area))


def construir_con_acomodos(
    pallet: Pallet,
    caja: Caja,
    restricciones: Restricciones,
    acomodos: Sequence[Acomodo],
    por_nivel: Sequence[int],
    estrategia: str = "a mano",
) -> Arrume:
    """Arrume con los acomodos dados y el nivel que lleva cada uno.

    'por_nivel' tiene un indice de 'acomodos' por nivel, de abajo arriba:
    [0, 0, 1, 0, 1] pone el primer acomodo en los niveles 1, 2 y 4.

    Los niveles no tienen por que llevar las mismas cajas: un nivel con
    menos cajas lleva menos, y las cuentas lo recogen.
    """
    if not acomodos:
        raise ConfiguracionInvalida("Hace falta al menos un acomodo.")

    area = area_disponible(pallet, restricciones)
    for acomodo in acomodos:
        fallos = problemas(acomodo.piezas, area, caja.base)
        if fallos:
            raise AcomodoInvalido(
                "El acomodo '{}' no se puede usar: {}".format(
                    acomodo.nombre, " ".join(fallos)
                )
            )

    cajas: list[Colocacion] = []
    for nivel, indice in enumerate(por_nivel):
        if not 0 <= indice < len(acomodos):
            raise ConfiguracionInvalida(
                f"El nivel {nivel + 1} apunta a un acomodo que no existe."
            )
        z = pallet.alto + nivel * caja.alto
        cajas.extend(
            _colocar(acomodos[indice].piezas, z, nivel, caja.alto, restricciones.vuelo)
        )

    return Arrume(
        pallet=pallet,
        caja=caja,
        restricciones=restricciones,
        acomodos=tuple(acomodos),
        por_nivel=tuple(por_nivel),
        cajas=tuple(cajas),
        estrategia=estrategia,
    )


def _colocar(
    patron: Sequence[Pieza],
    z: float,
    nivel: int,
    alto: float,
    vuelo: float,
) -> list[Colocacion]:
    """Lleva un acomodo del sistema del area al del pallet, a la altura z."""
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

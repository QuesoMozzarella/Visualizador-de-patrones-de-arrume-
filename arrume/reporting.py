"""Informe del arrume.

Calcula cifras y avisos y los devuelve como datos. Quien decide si eso se
imprime, se guarda o se muestra en una interfaz es la capa de entrada.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .domain.models import Arrume, Numero


@dataclass(frozen=True)
class Informe:
    """Resumen numerico de un arrume, sin formato."""

    cajas_por_nivel: int
    cajas_normales: int
    cajas_giradas: int
    niveles: int
    trabado: bool
    total_cajas: int
    altura_total: Numero
    aprovechamiento: float
    peso_total: Optional[Numero]
    avisos: Tuple[str, ...]


def generar_informe(arrume: Arrume) -> Informe:
    """Calcula las cifras del arrume y los avisos por limites excedidos."""
    caja = arrume.caja
    normales = sum(
        1
        for pieza in arrume.patron_base
        if (pieza.ancho, pieza.profundidad) == (caja.ancho, caja.profundidad)
    )

    avisos: List[str] = []
    limites = arrume.restricciones

    if limites.altura_max is not None and arrume.altura_total > limites.altura_max:
        avisos.append(
            "Supera la altura maxima de {} cm por {} cm.".format(
                _num(limites.altura_max), _num(arrume.altura_total - limites.altura_max)
            )
        )

    peso = arrume.peso_total
    if limites.peso_max is not None and peso is not None and peso > limites.peso_max:
        avisos.append(
            "Supera el peso maximo de {} kg por {:.1f} kg.".format(
                _num(limites.peso_max), peso - limites.peso_max
            )
        )

    return Informe(
        cajas_por_nivel=arrume.cajas_por_nivel,
        cajas_normales=normales,
        cajas_giradas=arrume.cajas_por_nivel - normales,
        niveles=arrume.niveles,
        trabado=limites.trabado,
        total_cajas=arrume.total_cajas,
        altura_total=arrume.altura_total,
        aprovechamiento=arrume.aprovechamiento,
        peso_total=peso,
        avisos=tuple(avisos),
    )


def formatear(arrume: Arrume, informe: Optional[Informe] = None) -> str:
    """Arma el texto del informe. Devuelve una cadena: no imprime nada."""
    if informe is None:
        informe = generar_informe(arrume)

    pallet, caja = arrume.pallet, arrume.caja
    lineas = [
        "Pallet .............. {} x {} x {} cm".format(
            _num(pallet.ancho), _num(pallet.profundidad), _num(pallet.alto)
        ),
        "Caja ................ {} x {} x {} cm".format(
            _num(caja.ancho), _num(caja.profundidad), _num(caja.alto)
        ),
        "Cajas por nivel ..... {}  ({} en posicion normal, {} giradas)".format(
            informe.cajas_por_nivel, informe.cajas_normales, informe.cajas_giradas
        ),
        "Niveles ............. {}  ({})".format(
            informe.niveles, "trabado" if informe.trabado else "en columna"
        ),
        "Total de cajas ...... {}".format(informe.total_cajas),
        "Altura total ........ {} cm".format(_num(informe.altura_total)),
        "Aprovechamiento ..... {:.1f} % de la superficie del pallet".format(
            informe.aprovechamiento
        ),
    ]
    if informe.peso_total is not None:
        lineas.append("Peso total .......... {:.1f} kg".format(informe.peso_total))
    for aviso in informe.avisos:
        lineas.append("  AVISO: {}".format(aviso))
    return "\n".join(lineas)


def _num(valor: Numero) -> str:
    """Muestra 120 en vez de 120.0, pero conserva los decimales reales."""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)

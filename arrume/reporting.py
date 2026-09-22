"""Informe del arrume.

Calcula cifras y avisos y los devuelve como datos. Quien decide si eso se
imprime, se guarda o se muestra en una interfaz es la capa de entrada.
"""

from __future__ import annotations

from dataclasses import dataclass

from .domain.models import Arrume, Numero
from .trabazon import cajas_calcadas, calidad


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
    peso_total: Numero | None
    avisos: tuple[str, ...]
    trabazon: str = ""
    trabazon_calidad: float = 0.0
    cajas_calcadas: int = 0

    @property
    def traba(self) -> bool:
        """True si el nivel alterno realmente pisa las juntas del de abajo."""
        return self.trabado and self.niveles > 1 and self.cajas_calcadas == 0


def generar_informe(arrume: Arrume) -> Informe:
    """Calcula las cifras del arrume y los avisos por limites excedidos."""
    caja = arrume.caja
    limites = arrume.restricciones
    normales = sum(
        1
        for pieza in arrume.patron_base
        if (pieza.ancho, pieza.profundidad) == (caja.ancho, caja.profundidad)
    )

    calcadas = cajas_calcadas(arrume.patron_base, arrume.patron_alterno)
    trabazon_calidad = calidad(arrume.patron_base, arrume.patron_alterno)

    avisos: list[str] = []

    if limites.trabado and arrume.niveles > 1 and calcadas == arrume.cajas_por_nivel:
        avisos.append(
            "El trabado no hace efecto: el patron ocupa el area sin holgura, "
            "asi que el nivel alterno queda calcado sobre el de abajo. "
            "Con otra medida de caja, o dejando vuelo, si trabaria."
        )

    if limites.altura_max is not None and arrume.altura_total > limites.altura_max:
        avisos.append(
            f"Supera la altura maxima de {_num(limites.altura_max)} cm "
            f"por {_num(arrume.altura_total - limites.altura_max)} cm."
        )

    peso = arrume.peso_total
    if limites.peso_max is not None and peso is not None and peso > limites.peso_max:
        avisos.append(
            f"Supera el peso maximo de {_num(limites.peso_max)} kg "
            f"por {peso - limites.peso_max:.1f} kg."
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
        trabazon=arrume.trabazon,
        trabazon_calidad=trabazon_calidad,
        cajas_calcadas=calcadas,
    )


def formatear(arrume: Arrume, informe: Informe | None = None) -> str:
    """Arma el texto del informe. Devuelve una cadena: no imprime nada."""
    if informe is None:
        informe = generar_informe(arrume)

    pallet, caja = arrume.pallet, arrume.caja
    dim_pallet = _medidas(pallet.ancho, pallet.profundidad, pallet.alto)
    dim_caja = _medidas(caja.ancho, caja.profundidad, caja.alto)
    lineas = [
        f"Pallet .............. {dim_pallet}",
        f"Caja ................ {dim_caja}",
        f"Cajas por nivel ..... {informe.cajas_por_nivel}  "
        f"({informe.cajas_normales} en posicion normal, "
        f"{informe.cajas_giradas} giradas)",
        "Niveles ............. {}  ({})".format(
            informe.niveles, "trabado" if informe.trabado else "en columna"
        ),
    ]

    if informe.trabado and informe.niveles > 1:
        lineas.append(
            f"Trabazon ............ {100 * informe.trabazon_calidad:.0f} %  "
            f"({informe.trabazon}, {informe.cajas_calcadas} de "
            f"{informe.cajas_por_nivel} cajas calcadas)"
        )

    lineas += [
        f"Total de cajas ...... {informe.total_cajas}",
        f"Altura total ........ {_num(informe.altura_total)} cm",
        f"Aprovechamiento ..... {informe.aprovechamiento:.1f} % "
        "de la superficie del pallet",
    ]
    if informe.peso_total is not None:
        lineas.append(f"Peso total .......... {informe.peso_total:.1f} kg")
    for aviso in informe.avisos:
        lineas.append(f"  AVISO: {aviso}")
    return "\n".join(lineas)


def _medidas(*valores: Numero) -> str:
    """Formatea unas dimensiones: '120 x 100 x 15 cm'."""
    return " x ".join(_num(v) for v in valores) + " cm"


def _num(valor: Numero) -> str:
    """Muestra 120 en vez de 120.0, pero conserva los decimales reales."""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)

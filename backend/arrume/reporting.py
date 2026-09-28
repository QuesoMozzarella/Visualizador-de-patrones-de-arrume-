"""Informe del arrume.

Calcula cifras y avisos y los devuelve como datos. Quien decide si eso se
imprime, se guarda o se muestra en una interfaz es la capa de entrada.
"""

from __future__ import annotations

from dataclasses import dataclass

from .domain.models import Arrume, Numero


@dataclass(frozen=True)
class UsoDeAcomodo:
    """Un acomodo del arrume (normal, cruzado...) y los niveles que lo llevan."""

    nombre: str
    niveles: tuple[int, ...]
    cajas: int
    normales: int
    giradas: int


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
    avisos: tuple[str, ...]
    acomodos: tuple[UsoDeAcomodo, ...] = ()


def generar_informe(arrume: Arrume) -> Informe:
    """Calcula las cifras del arrume y los avisos."""
    usos = _usos(arrume)
    primero = next(uso for uso in usos if 1 in uso.niveles)

    avisos: list[str] = []
    cuentas = {uso.cajas for uso in usos}
    if len(cuentas) > 1:
        avisos.append(
            f"No todos los niveles llevan las mismas cajas (de {min(cuentas)} "
            f"a {max(cuentas)}): el nivel con menos deja huecos."
        )

    return Informe(
        cajas_por_nivel=primero.cajas,
        cajas_normales=primero.normales,
        cajas_giradas=primero.giradas,
        niveles=arrume.niveles,
        trabado=arrume.restricciones.trabado,
        total_cajas=arrume.total_cajas,
        altura_total=arrume.altura_total,
        aprovechamiento=arrume.aprovechamiento,
        avisos=tuple(avisos),
        acomodos=usos,
    )


def _usos(arrume: Arrume) -> tuple[UsoDeAcomodo, ...]:
    """Cada acomodo que se usa, en el orden en que aparece de abajo arriba."""
    caja = arrume.caja
    usos = []
    for indice in dict.fromkeys(arrume.por_nivel):
        acomodo = arrume.acomodos[indice]
        normales = sum(
            1
            for pieza in acomodo.piezas
            if (pieza.ancho, pieza.profundidad) == (caja.ancho, caja.profundidad)
        )
        usos.append(
            UsoDeAcomodo(
                nombre=acomodo.nombre,
                niveles=tuple(
                    nivel
                    for nivel, otro in enumerate(arrume.por_nivel, start=1)
                    if otro == indice
                ),
                cajas=acomodo.cajas,
                normales=normales,
                giradas=acomodo.cajas - normales,
            )
        )
    return tuple(usos)


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
        "Niveles ............. {}  ({})".format(
            informe.niveles, "cruzados" if informe.trabado else "en columna"
        ),
    ]

    for uso in informe.acomodos:
        cuales = (
            "todos los niveles"
            if len(uso.niveles) == informe.niveles
            else _lista("nivel", "niveles", uso.niveles)
        )
        lineas.append(
            f"  {uso.nombre.capitalize()}, {cuales}: {uso.cajas} cajas "
            f"({uso.normales} derechas, {uso.giradas} giradas)"
        )

    lineas += [
        f"Total de cajas ...... {informe.total_cajas}",
        f"Altura total ........ {_num(informe.altura_total)} cm",
        f"Aprovechamiento ..... {informe.aprovechamiento:.1f} % "
        "de la superficie del pallet",
    ]
    for aviso in informe.avisos:
        lineas.append(f"  AVISO: {aviso}")
    return "\n".join(lineas)


def _lista(singular: str, plural: str, numeros: tuple[int, ...]) -> str:
    """'nivel 3', 'niveles 1 y 2', 'niveles 1, 3 y 5'."""
    if len(numeros) == 1:
        return f"{singular} {numeros[0]}"
    cabeza = ", ".join(str(n) for n in numeros[:-1])
    return f"{plural} {cabeza} y {numeros[-1]}"


def _medidas(*valores: Numero) -> str:
    """Formatea unas dimensiones: '120 x 100 x 15 cm'."""
    return " x ".join(_num(v) for v in valores) + " cm"


def _num(valor: Numero) -> str:
    """Muestra 120 en vez de 120.0, pero conserva los decimales reales."""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)

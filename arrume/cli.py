"""Interfaz de linea de comandos: la unica capa que imprime y que sale del proceso.

Reemplaza a las constantes globales del script original: cada parametro que
antes se editaba a mano en el codigo es ahora una opcion.

    python -m arrume --pallet 120 100 --caja 40 30 25 --niveles 5
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from .domain.errors import ArrumeError
from .domain.models import Caja, Numero, Pallet, Restricciones
from .reporting import formatear
from .stacking import construir_arrume
from .trabazon import MejorAlterno, Rotacion180

_SALIDA_POR_DEFECTO = "arrume.html"

# Modos de trabazon que se pueden pedir por linea de comandos
TRABAZONES = {"mejor": MejorAlterno, "rotacion": Rotacion180}


def _numero(texto: str) -> Numero:
    """Convierte a int cuando el valor es entero, para no perder exactitud."""
    try:
        valor = float(texto)
    except ValueError:
        raise argparse.ArgumentTypeError("'{}' no es un numero.".format(texto))
    return int(valor) if valor.is_integer() else valor


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arrume",
        description="Genera y dibuja un patron de arrume (pallet loading) en 3D.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--pallet", nargs=2, type=_numero, default=[120, 100],
        metavar=("ANCHO", "PROFUNDIDAD"),
        help="superficie del pallet en cm",
    )
    parser.add_argument(
        "--pallet-alto", type=_numero, default=15, metavar="CM",
        help="grueso de la plataforma del pallet en cm",
    )
    parser.add_argument(
        "--caja", nargs=3, type=_numero, default=[40, 30, 25],
        metavar=("ANCHO", "PROFUNDIDAD", "ALTO"),
        help="dimensiones de la caja en cm",
    )
    parser.add_argument(
        "--niveles", type=int, default=5, metavar="N",
        help="cuantos niveles (pisos) de cajas apilar",
    )
    trabado = parser.add_mutually_exclusive_group()
    trabado.add_argument(
        "--trabado", dest="trabado", action="store_true", default=True,
        help="alterna el patron entre niveles",
    )
    trabado.add_argument(
        "--sin-trabado", dest="trabado", action="store_false",
        help="apila en columna, todos los niveles iguales",
    )
    parser.add_argument(
        "--trabazon", choices=sorted(TRABAZONES), default="mejor",
        help="'mejor' prueba varios patrones alternos; 'rotacion' es el giro "
             "de 180 grados del proyecto original",
    )
    parser.add_argument(
        "--vuelo", type=_numero, default=0, metavar="CM",
        help="cuanto pueden sobresalir las cajas del pallet por lado",
    )
    parser.add_argument(
        "--altura-max", type=_numero, default=None, metavar="CM",
        help="altura maxima admitida; si se supera, el informe avisa",
    )
    parser.add_argument(
        "--peso-caja", type=_numero, default=None, metavar="KG",
        help="peso de una caja, para calcular el peso total",
    )
    parser.add_argument(
        "--peso-max", type=_numero, default=None, metavar="KG",
        help="peso maximo admitido; necesita --peso-caja",
    )
    parser.add_argument(
        "--salida", default=_SALIDA_POR_DEFECTO, metavar="ARCHIVO",
        help="archivo HTML donde guardar el grafico",
    )
    parser.add_argument(
        "--no-abrir", dest="abrir", action="store_false", default=True,
        help="no abrir el navegador al terminar",
    )
    parser.add_argument(
        "--sin-grafico", action="store_true",
        help="solo imprimir el informe, sin generar el HTML",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada. Devuelve el codigo de salida del proceso."""
    args = construir_parser().parse_args(argv)

    try:
        pallet = Pallet(args.pallet[0], args.pallet[1], args.pallet_alto)
        caja = Caja(args.caja[0], args.caja[1], args.caja[2])
        restricciones = Restricciones(
            niveles=args.niveles,
            trabado=args.trabado,
            vuelo=args.vuelo,
            altura_max=args.altura_max,
            peso_caja=args.peso_caja,
            peso_max=args.peso_max,
        )
        arrume = construir_arrume(
            pallet, caja, restricciones, trabazon=TRABAZONES[args.trabazon]()
        )
    except ArrumeError as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 2

    print(formatear(arrume))

    if not args.sin_grafico:
        from .render.plotly3d import construir_figura, exportar_html

        ruta = exportar_html(construir_figura(arrume), args.salida, args.abrir)
        print("\nGrafico guardado en {}".format(ruta))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Interfaz de linea de comandos: la unica capa que imprime y que sale del proceso.

Reemplaza a las constantes globales del script original: cada parametro que
antes se editaba a mano en el codigo es ahora una opcion.

    python -m arrume --pallet 120 100 --caja 40 30 25 --niveles 5
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .domain.errors import ArrumeError
from .domain.models import Caja, Numero, Pallet, Restricciones
from .reporting import formatear
from .stacking import construir_arrume
from .trabazon import TRABAZONES

_SALIDA_POR_DEFECTO = "arrume.html"


def _numero(texto: str) -> Numero:
    """Convierte a int cuando el valor es entero, para no perder exactitud."""
    try:
        valor = float(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' no es un numero.") from None
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
        "--html", choices=["cdn", "completo"], default="cdn",
        help="'cdn' deja la libreria fuera del archivo (~50 KB, necesita "
             "internet al abrirlo); 'completo' la incrusta (~4.8 MB, sirve "
             "sin conexion)",
    )
    parser.add_argument(
        "--sin-grafico", action="store_true",
        help="solo imprimir el informe, sin generar el HTML",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
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
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(formatear(arrume))

    if not args.sin_grafico:
        # Se importa aqui para que el informe no dependa de tener plotly
        from .render.plotly3d import ExportadorHTML, Plotly3D

        figura = Plotly3D().render(arrume)
        ruta = ExportadorHTML(args.html).exportar(figura, args.salida, args.abrir)
        print(f"\nGrafico guardado en {ruta}")
        if args.html == "cdn":
            print(
                "(carga la libreria por internet; con --html completo queda "
                "autocontenido)"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

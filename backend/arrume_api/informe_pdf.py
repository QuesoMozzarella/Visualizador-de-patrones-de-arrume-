"""Informe del arrume en PDF, para imprimir y llevar a bodega.

Lleva los datos del arrume, el acomodo del nivel dibujado (normal y, si se
usa, cruzado, con las cajas numeradas), como va cada piso de arriba abajo
y, al final, los modelos 3D del arrume, la caja y el pallet que manda el
frontend como imagenes.

Los planos se dibujan como vectores: se imprimen nitidos a cualquier
tamano. Es un adaptador de salida, igual que la API: el paquete arrume no
sabe que existe.
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from datetime import datetime

from reportlab.graphics.shapes import Drawing, Group, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from arrume.domain.models import Arrume, Numero, Pieza
from arrume.pisos import CRUZADO, NORMAL, cruzar
from arrume.reporting import Informe, generar_informe
from arrume.stacking import acomodo_normal, area_disponible

MARGEN = 15 * mm
ANCHO_UTIL = A4[0] - 2 * MARGEN

# Los mismos colores que la pagina, para que el papel se lea igual
DERECHA = colors.HexColor("#e8ddc8")
GIRADA = colors.HexColor("#cbb994")
SUELO = colors.HexColor("#f2f2ef")
TINTA = colors.black
GRAFITO = colors.HexColor("#4a4e4b")
SEGURIDAD = colors.HexColor("#ffc400")
FILETE = colors.HexColor("#c9cdc9")

_TITULO = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=18, leading=22)
_SUBTITULO = ParagraphStyle(
    "subtitulo", fontName="Helvetica", fontSize=10, leading=13, textColor=GRAFITO
)
_SECCION = ParagraphStyle(
    "seccion", fontName="Helvetica-Bold", fontSize=12.5, leading=16, spaceBefore=10,
    spaceAfter=5,
)
_TEXTO = ParagraphStyle("texto", fontName="Helvetica", fontSize=9.5, leading=12.5)
_PIE_PLANO = ParagraphStyle(
    "pie", fontName="Helvetica", fontSize=8.5, leading=11, textColor=GRAFITO
)
_AVISO = ParagraphStyle("aviso", parent=_TEXTO, fontSize=9, leading=12)

FORMA = {NORMAL: "Normal", CRUZADO: "Cruzado"}


def _num(valor: Numero) -> str:
    """120 en vez de 120.0, pero conserva los decimales reales."""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(round(valor, 2))


def _medidas(*valores: Numero) -> str:
    return " × ".join(_num(v) for v in valores) + " cm"


# =====================================================================
# Planos
# =====================================================================


def plano(
    piezas: Sequence[Pieza],
    ancho_area: Numero,
    fondo_area: Numero,
    caja_ancho: Numero,
    ancho: float,
    numeros: bool = True,
    cotas: bool = True,
) -> Drawing:
    """El nivel visto desde arriba, escalado a 'ancho' puntos.

    Con 'numeros' cada caja lleva su numero; con 'cotas' se rotulan las
    medidas del pallet por fuera del dibujo.
    """
    margen_cota = 11 if cotas else 1
    escala = (ancho - margen_cota - 1) / float(ancho_area)
    alto = fondo_area * escala + margen_cota + 1
    dibujo = Drawing(ancho, alto)
    ox, oy = margen_cota, margen_cota

    dibujo.add(
        Rect(ox, oy, ancho_area * escala, fondo_area * escala,
             fillColor=SUELO, strokeColor=TINTA, strokeWidth=0.8)
    )
    tamano_letra = max(4.0, min(9.0, min(
        min(p.ancho, p.profundidad) for p in piezas
    ) * escala * 0.42)) if piezas else 8.0

    for n, p in enumerate(piezas, start=1):
        girada = abs(p.ancho - caja_ancho) > 1e-6
        x, y = ox + p.x * escala, oy + p.y * escala
        w, h = p.ancho * escala, p.profundidad * escala
        dibujo.add(
            Rect(x, y, w, h, fillColor=GIRADA if girada else DERECHA,
                 strokeColor=TINTA, strokeWidth=0.6)
        )
        if numeros:
            dibujo.add(
                String(x + w / 2, y + h / 2 - tamano_letra * 0.35, str(n),
                       fontName="Helvetica-Bold", fontSize=tamano_letra,
                       textAnchor="middle", fillColor=TINTA)
            )

    if cotas:
        ancho_px, fondo_px = ancho_area * escala, fondo_area * escala
        dibujo.add(Line(ox, 4, ox + ancho_px, 4, strokeColor=GRAFITO, strokeWidth=0.4))
        dibujo.add(
            String(ox + ancho_px / 2, 6, f"{_num(ancho_area)} cm", fontName="Helvetica",
                   fontSize=6.5, textAnchor="middle", fillColor=GRAFITO)
        )
        dibujo.add(Line(4, oy, 4, oy + fondo_px, strokeColor=GRAFITO, strokeWidth=0.4))
        fondo = String(0, 0, f"{_num(fondo_area)} cm", fontName="Helvetica",
                       fontSize=6.5, textAnchor="middle", fillColor=GRAFITO)
        # Texto girado 90 grados a lo largo del fondo
        rotulo = Group(fondo)
        rotulo.transform = (0, 1, -1, 0, 9, oy + fondo_px / 2)
        dibujo.add(rotulo)
    return dibujo


def _con_pie(dibujo: Drawing, texto: str) -> Table:
    """Un plano con su rotulo debajo, como una sola pieza."""
    tabla = Table([[dibujo], [Paragraph(texto, _PIE_PLANO)]])
    tabla.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return tabla


# =====================================================================
# Secciones
# =====================================================================


def _encabezado(nombre: str, fecha: datetime) -> list[Flowable]:
    titulo = "Informe de arrume" + (f": {_escapar(nombre)}" if nombre else "")
    return [
        Paragraph(titulo, _TITULO),
        Paragraph(f"Generado el {fecha:%d/%m/%Y a las %H:%M}", _SUBTITULO),
        Spacer(1, 6),
    ]


def _datos(arrume: Arrume, informe: Informe) -> list[Flowable]:
    pallet, caja = arrume.pallet, arrume.caja
    como_van = "cruzados" if informe.trabado else "todos normales, en columna"
    filas = [
        ["Pallet", _medidas(pallet.ancho, pallet.profundidad, pallet.alto)],
        ["Caja", _medidas(caja.ancho, caja.profundidad, caja.alto)],
        ["Pisos", f"{informe.niveles}  ({como_van})"],
        [
            "Cajas por piso",
            f"{informe.cajas_por_nivel}  ({informe.cajas_normales} derechas, "
            f"{informe.cajas_giradas} giradas)",
        ],
        ["Total de cajas", str(informe.total_cajas)],
        ["Altura total", f"{_num(informe.altura_total)} cm (con el pallet)"],
        ["Pallet cubierto", f"{informe.aprovechamiento:.1f} %"],
    ]
    tabla = Table(filas, colWidths=[38 * mm, ANCHO_UTIL - 38 * mm])
    tabla.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9.5),
        ("FONT", (1, 0), (1, -1), "Helvetica", 9.5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, FILETE),
        ("BOX", (0, 0), (-1, -1), 0.8, TINTA),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    bloque: list[Flowable] = [Paragraph("Datos", _SECCION), tabla]

    for aviso in informe.avisos:
        texto = Paragraph(f"<b>Precaución:</b> {_escapar(aviso)}", _AVISO)
        caja_aviso = Table([[texto]], colWidths=[ANCHO_UTIL])
        caja_aviso.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SEGURIDAD),
            ("BOX", (0, 0), (-1, -1), 0.8, TINTA),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        bloque += [Spacer(1, 4), caja_aviso]
    return bloque


def _acomodo(arrume: Arrume) -> list[Flowable]:
    area = area_disponible(arrume.pallet, arrume.restricciones)
    formas = {arrume.acomodo_de(n).nombre for n in range(1, arrume.niveles + 1)}
    normal = acomodo_normal(arrume)
    cruzado = tuple(cruzar(normal, area))
    cruza = CRUZADO in formas

    columnas = 2
    hueco = 6 * mm
    ancho = (ANCHO_UTIL - hueco * (columnas - 1)) / columnas
    caja_ancho = arrume.caja.ancho

    def dibujo(piezas: Sequence[Pieza]) -> Drawing:
        return plano(piezas, area.ancho, area.profundidad, caja_ancho, ancho)

    celdas = [_con_pie(
        dibujo(normal),
        f"<b>Normal</b>: {len(normal)} cajas, numeradas en el orden del acomodo.",
    )]
    if cruza:
        celdas.append(_con_pie(
            dibujo(cruzado),
            "<b>Cruzado</b>: el mismo acomodo con media vuelta (180°). "
            "Cada caja conserva su número.",
        ))
    else:
        celdas.append(Paragraph(
            "Todos los pisos van normales: el arrume va en columna, con el mismo "
            "acomodo en cada piso.", _TEXTO))

    fila = Table([celdas], colWidths=[ancho] * columnas, hAlign="LEFT")
    fila.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), hueco),
    ]))

    leyenda = Paragraph(
        '<font color="#cbb994">&#9632;</font> caja girada &nbsp;&nbsp; '
        '<font color="#e8ddc8">&#9632;</font> caja derecha &nbsp;&nbsp; '
        f"Caja de {_medidas(arrume.caja.ancho, arrume.caja.profundidad)}; "
        f"pallet de {_medidas(arrume.pallet.ancho, arrume.pallet.profundidad)}.",
        _PIE_PLANO,
    )
    titulo = Paragraph("Acomodo del nivel", _SECCION)
    return [KeepTogether([titulo, fila, Spacer(1, 3), leyenda])]


POR_FILA = 4


def _pisos(arrume: Arrume) -> list[Flowable]:
    """Una tarjeta por piso, de arriba abajo, como la pagina."""
    area = area_disponible(arrume.pallet, arrume.restricciones)
    hueco = 4 * mm
    ancho = (ANCHO_UTIL - hueco * (POR_FILA - 1)) / POR_FILA

    tarjetas: list[Table] = []
    for nivel in range(arrume.niveles, 0, -1):
        acomodo = arrume.acomodo_de(nivel)
        cruzado = acomodo.nombre == CRUZADO
        forma = FORMA.get(acomodo.nombre, acomodo.nombre)
        titulo = Paragraph(
            f"<b>Piso {nivel}</b> · {'<b>' + forma + '</b>' if cruzado else forma}",
            _TEXTO,
        )
        dibujo = plano(acomodo.piezas, area.ancho, area.profundidad,
                       arrume.caja.ancho, ancho - 8, numeros=False, cotas=False)
        tarjeta = Table([[titulo], [dibujo]], colWidths=[ancho])
        tarjeta.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, TINTA),
            # Los cruzados, resaltados para que no se pasen por alto
            ("BACKGROUND", (0, 0), (0, 0), SEGURIDAD if cruzado else colors.white),
            ("LINEBELOW", (0, 0), (0, 0), 0.4, TINTA),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        tarjetas.append(tarjeta)

    filas = [
        tarjetas[k:k + POR_FILA] + [""] * (POR_FILA - len(tarjetas[k:k + POR_FILA]))
        for k in range(0, len(tarjetas), POR_FILA)
    ]
    rejilla = Table(filas, colWidths=[ancho + hueco] * (POR_FILA - 1) + [ancho],
                    hAlign="LEFT")
    rejilla.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), hueco),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    cruzados = [n for n in range(1, arrume.niveles + 1)
                if arrume.acomodo_de(n).nombre == CRUZADO]
    if len(cruzados) > 1:
        lista = ", ".join(map(str, cruzados[:-1])) + f" y {cruzados[-1]}"
        resumen = f"Van cruzados los pisos {lista}."
    elif cruzados:
        resumen = f"Va cruzado el piso {cruzados[0]}."
    else:
        resumen = "Todos los pisos van normales."
    return [
        Paragraph("Pisos, de arriba abajo", _SECCION),
        Paragraph(
            f"{resumen} El piso 1 es el que va sobre el pallet.", _PIE_PLANO),
        Spacer(1, 4),
        rejilla,
    ]


def _imagen(imagen: bytes, ancho_max: float, alto_max: float) -> Image:
    """La imagen tan grande como quepa en la caja, sin deformarla."""
    ancho_px, alto_px = ImageReader(io.BytesIO(imagen)).getSize()
    escala = min(ancho_max / ancho_px, alto_max / alto_px)
    return Image(io.BytesIO(imagen), width=ancho_px * escala, height=alto_px * escala)


def _modelos_3d(
    arrume: Arrume,
    imagen_3d: bytes | None,
    imagen_caja: bytes | None,
    imagen_pallet: bytes | None,
) -> list[Flowable]:
    """El arrume en 3D y, debajo, la caja y el pallet sueltos con sus medidas."""
    bloque: list[Flowable] = [Paragraph("Modelos 3D", _SECCION)]
    if imagen_3d:
        bloque.append(_imagen(imagen_3d, ANCHO_UTIL, 110 * mm))

    piezas = []
    caja, pallet = arrume.caja, arrume.pallet
    if imagen_caja:
        piezas.append(_con_pie(
            _imagen(imagen_caja, ANCHO_UTIL / 2 - 4 * mm, 70 * mm),
            f"<b>Caja</b>: {_medidas(caja.ancho, caja.profundidad, caja.alto)}",
        ))
    if imagen_pallet:
        piezas.append(_con_pie(
            _imagen(imagen_pallet, ANCHO_UTIL / 2 - 4 * mm, 70 * mm),
            f"<b>Pallet</b>: {_medidas(pallet.ancho, pallet.profundidad, pallet.alto)}",
        ))
    if piezas:
        fila = Table([piezas], colWidths=[ANCHO_UTIL / 2] * len(piezas), hAlign="LEFT")
        fila.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        bloque += [Spacer(1, 6), fila]

    if len(bloque) == 1:
        return []
    return [KeepTogether(bloque[:2]), *bloque[2:]]


# =====================================================================
# Documento
# =====================================================================


def informe_pdf(
    arrume: Arrume,
    nombre: str = "",
    imagen_3d: bytes | None = None,
    fecha: datetime | None = None,
    imagen_caja: bytes | None = None,
    imagen_pallet: bytes | None = None,
    comprimir: bool = True,
) -> bytes:
    """El informe completo, como bytes de un PDF."""
    informe = generar_informe(arrume)
    fecha = fecha or datetime.now()
    salida = io.BytesIO()

    documento = SimpleDocTemplate(
        salida,
        pagesize=A4,
        leftMargin=MARGEN,
        rightMargin=MARGEN,
        topMargin=MARGEN,
        bottomMargin=MARGEN + 4 * mm,
        title=f"Informe de arrume{': ' + nombre if nombre else ''}",
        author="Arrume",
        pageCompression=1 if comprimir else 0,
    )

    contenido: list[Flowable] = []
    contenido += _encabezado(nombre, fecha)
    contenido += _datos(arrume, informe)
    contenido += _acomodo(arrume)
    contenido += _pisos(arrume)
    contenido += _modelos_3d(arrume, imagen_3d, imagen_caja, imagen_pallet)

    def pie(canvas: Canvas, doc: SimpleDocTemplate) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GRAFITO)
        marca = "Arrume" + (f" · {nombre}" if nombre else "")
        canvas.drawString(MARGEN, MARGEN / 2, marca)
        canvas.drawRightString(A4[0] - MARGEN, MARGEN / 2, f"Página {doc.page}")
        canvas.restoreState()

    documento.build(contenido, onFirstPage=pie, onLaterPages=pie)
    return salida.getvalue()


def _escapar(texto: str) -> str:
    """Paragraph interpreta etiquetas: el texto del usuario va escapado."""
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

"""El informe devuelve datos y texto; no imprime ni decide nada."""

from __future__ import annotations

import io
import sys

from arrume import Caja, Pallet, Restricciones
from arrume.pisos import reparto
from arrume.reporting import formatear, generar_informe
from arrume.stacking import construir_por_pisos

PALLET = Pallet(120, 100, 15)
CAJA = Caja(40, 30, 25)


def _arrume(niveles=5, pallet=PALLET, caja=CAJA):
    return construir_por_pisos(
        pallet, caja, Restricciones(niveles=niveles), reparto(niveles)
    )


def test_las_cifras_del_informe_coinciden_con_el_arrume():
    arrume = _arrume()
    informe = generar_informe(arrume)
    assert informe.cajas_por_nivel == 10
    assert informe.cajas_normales + informe.cajas_giradas == informe.cajas_por_nivel
    assert informe.total_cajas == 50
    assert informe.altura_total == 140
    assert informe.aprovechamiento == 100.0
    assert informe.avisos == ()


def _por_pisos(*pisos, acomodo=None):
    return construir_por_pisos(
        Pallet(120, 100, 15),
        Caja(40, 30, 25),
        Restricciones(niveles=len(pisos)),
        list(pisos),
        acomodo,
    )


def test_el_informe_dice_que_pisos_van_normales_y_cuales_cruzados():
    informe = generar_informe(_por_pisos("normal", "cruzado", "normal"))
    assert [(uso.nombre, uso.niveles) for uso in informe.acomodos] == [
        ("normal", (1, 3)),
        ("cruzado", (2,)),
    ]
    texto = formatear(_por_pisos("normal", "cruzado", "normal"))
    assert "(cruzados)" in texto
    assert "Normal, niveles 1 y 3: 10 cajas" in texto
    assert "Cruzado, nivel 2: 10 cajas" in texto


def test_todos_normales_va_en_columna():
    texto = formatear(_por_pisos("normal", "normal", "normal"))
    assert "(en columna)" in texto
    assert "Normal, todos los niveles" in texto
    assert "Trabazon" not in texto


def test_no_habla_de_trabazon():
    texto = formatear(_por_pisos("normal", "normal", "cruzado")).lower()
    assert "trabazon" not in texto
    assert "calcad" not in texto
    assert generar_informe(_por_pisos("normal", "normal", "cruzado")).avisos == ()


def test_no_menciona_peso_ni_limites():
    texto = formatear(_arrume()).lower()
    assert "peso" not in texto
    assert "maxima" not in texto


def test_formatear_devuelve_texto_y_no_imprime():
    arrume = _arrume()
    capturado, sys.stdout = sys.stdout, io.StringIO()
    try:
        texto = formatear(arrume)
        escrito = sys.stdout.getvalue()
    finally:
        sys.stdout = capturado

    assert escrito == "", "el informe no debe escribir en stdout"
    assert "Pallet .............. 120 x 100 x 15 cm" in texto
    assert "Total de cajas ...... 50" in texto


def test_las_medidas_enteras_no_muestran_decimales():
    arrume = _arrume(2, Pallet(120.0, 100.0, 15.0), Caja(40.0, 30.0, 25.0))
    assert "120 x 100 x 15 cm" in formatear(arrume)


def test_las_medidas_decimales_se_conservan():
    arrume = _arrume(2, caja=Caja(37.5, 27.5, 22))
    assert "37.5 x 27.5 x 22 cm" in formatear(arrume)

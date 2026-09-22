"""El informe devuelve datos y texto; no imprime ni decide nada."""

from __future__ import annotations

import io
import sys

from arrume import Caja, Pallet, Restricciones, construir_arrume
from arrume.reporting import formatear, generar_informe


def _arrume(**limites):
    limites.setdefault("niveles", 5)
    return construir_arrume(
        Pallet(120, 100, 15), Caja(40, 30, 25), Restricciones(**limites)
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


def test_avisa_cuando_se_pasa_de_altura():
    informe = generar_informe(_arrume(niveles=8, altura_max=180))
    assert len(informe.avisos) == 1
    assert "altura maxima" in informe.avisos[0]


def test_avisa_cuando_se_pasa_de_peso():
    informe = generar_informe(_arrume(niveles=5, peso_caja=20, peso_max=500))
    assert len(informe.avisos) == 1
    assert "peso maximo" in informe.avisos[0]


def test_puede_avisar_de_las_dos_cosas_a_la_vez():
    informe = generar_informe(
        _arrume(niveles=8, altura_max=180, peso_caja=20, peso_max=500)
    )
    assert len(informe.avisos) == 2


def test_no_avisa_cuando_esta_dentro_de_los_limites():
    informe = generar_informe(
        _arrume(niveles=5, altura_max=180, peso_caja=1, peso_max=500)
    )
    assert informe.avisos == ()


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
    arrume = construir_arrume(
        Pallet(120.0, 100.0, 15.0), Caja(40.0, 30.0, 25.0), Restricciones(niveles=2)
    )
    assert "120 x 100 x 15 cm" in formatear(arrume)


def test_las_medidas_decimales_se_conservan():
    arrume = construir_arrume(
        Pallet(120, 100, 15), Caja(37.5, 27.5, 22), Restricciones(niveles=2)
    )
    assert "37.5 x 27.5 x 22 cm" in formatear(arrume)

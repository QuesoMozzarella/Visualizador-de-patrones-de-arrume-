"""El trabado: lo que hace hoy y lo que deberia hacer.

El trabado existe para que las cajas de un nivel pisen la union de las del
nivel de abajo y el arrume no se abra. La implementacion actual gira el
nivel completo 180 grados, y eso solo traba cuando el patron base NO es
simetrico respecto a su centro.

El test marcado con xfail deja documentado el fallo: cuando se implemente el
patron alterno de verdad, pasara a XPASS y habra que quitarle la marca.
"""

from __future__ import annotations

import pytest

from arrume import Caja, Pallet, Restricciones, construir_arrume


def _huellas_por_nivel(arrume):
    """El conjunto de rectangulos que ocupa cada nivel, en el plano XY."""
    return [
        sorted(
            (c.x, c.y, c.ancho, c.profundidad)
            for c in arrume.cajas
            if c.nivel == nivel
        )
        for nivel in range(arrume.niveles)
    ]


def test_sin_trabado_todos_los_niveles_son_identicos():
    arrume = construir_arrume(
        Pallet(120, 100, 15), Caja(40, 30, 25), Restricciones(niveles=4, trabado=False)
    )
    huellas = _huellas_por_nivel(arrume)
    assert all(nivel == huellas[0] for nivel in huellas)


def test_con_trabado_los_niveles_alternan_entre_dos_patrones():
    """Sea cual sea el patron, los pares deben repetirse y los impares tambien."""
    arrume = construir_arrume(
        Pallet(120, 100, 15), Caja(40, 30, 25), Restricciones(niveles=5, trabado=True)
    )
    huellas = _huellas_por_nivel(arrume)
    assert huellas[0] == huellas[2] == huellas[4]
    assert huellas[1] == huellas[3]


def test_con_un_patron_asimetrico_el_trabado_si_cambia_el_nivel():
    arrume = construir_arrume(
        Pallet(120, 100, 15), Caja(40, 30, 25), Restricciones(niveles=2, trabado=True)
    )
    huellas = _huellas_por_nivel(arrume)
    assert huellas[0] != huellas[1]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "FALLO CONOCIDO: el trabado gira el nivel 180 grados. Con un patron "
        "simetrico (aqui 6 cajas de 40x40 en un pallet de 120x80) el nivel "
        "girado queda igual al original y no hay trabazon. Hace falta un "
        "patron alterno propio, no una rotacion."
    ),
)
def test_el_trabado_deberia_cambiar_el_patron_siempre():
    arrume = construir_arrume(
        Pallet(120, 80, 15), Caja(40, 40, 30), Restricciones(niveles=2, trabado=True)
    )
    huellas = _huellas_por_nivel(arrume)
    assert huellas[0] != huellas[1], "el nivel 2 quedo calcado del nivel 1"

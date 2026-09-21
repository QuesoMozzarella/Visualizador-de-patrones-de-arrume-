"""Las transformaciones mueven el patron sin romperlo."""

from __future__ import annotations

import pytest

from arrume.domain.models import Area, Pieza
from arrume.packing import Guillotina
from arrume.packing.transformaciones import (
    a_esquina,
    desplazar,
    espejo_x,
    espejo_y,
    holgura,
    rotar_180,
)
from invariantes import fuera_del_area, mide_la_caja, sin_solapamientos_2d

AREAS_Y_CAJAS = [
    ((120, 100), (40, 30)),
    ((120, 100), (33, 27)),
    ((100, 100), (30, 30)),
    ((110, 90), (45, 25)),
    ((80, 60), (25, 20)),
]

TRANSFORMACIONES = [
    ("rotar_180", rotar_180),
    ("espejo_x", espejo_x),
    ("espejo_y", espejo_y),
    ("esquina ++", lambda p, a: a_esquina(p, a, 1, 1)),
    ("esquina --", lambda p, a: a_esquina(p, a, -1, -1)),
    ("esquina +-", lambda p, a: a_esquina(p, a, 1, -1)),
]


@pytest.mark.parametrize("nombre, transformar", TRANSFORMACIONES, ids=lambda v: v)
@pytest.mark.parametrize("medidas_area, medidas_caja", AREAS_Y_CAJAS)
def test_el_patron_transformado_sigue_siendo_valido(
    nombre, transformar, medidas_area, medidas_caja
):
    area, caja = Area(*medidas_area), Area(*medidas_caja)
    base = Guillotina().generar(area, caja)

    movido = transformar(base, area)

    assert len(movido) == len(base)
    assert fuera_del_area(movido, area) == []
    assert sin_solapamientos_2d(movido) == []
    assert all(mide_la_caja(pieza, caja) for pieza in movido)


@pytest.mark.parametrize("medidas_area, medidas_caja", AREAS_Y_CAJAS)
def test_girar_dos_veces_deja_el_patron_como_estaba(medidas_area, medidas_caja):
    area = Area(*medidas_area)
    base = Guillotina().generar(area, Area(*medidas_caja))
    ida_y_vuelta = rotar_180(rotar_180(base, area), area)
    assert sorted(map(_clave, ida_y_vuelta)) == sorted(map(_clave, base))


def test_desplazar_mueve_todo_el_patron_por_igual():
    piezas = [Pieza(0, 0, 40, 30), Pieza(40, 0, 40, 30)]
    movido = desplazar(piezas, 5, 2.5)
    assert [(p.x, p.y) for p in movido] == [(5, 2.5), (45, 2.5)]


def test_la_holgura_es_lo_que_le_sobra_al_patron():
    area = Area(120, 100)
    piezas = [Pieza(0, 0, 40, 30)]
    assert holgura(piezas, area) == (80, 70)


def test_sin_holgura_arrimar_a_la_esquina_no_cambia_nada():
    area = Area(120, 100)
    base = Guillotina().generar(area, Area(40, 50))  # llena exacto
    assert holgura(base, area) == (0, 0)
    assert sorted(map(_clave, a_esquina(base, area, 1, 1))) == sorted(map(_clave, base))


def _clave(pieza):
    return (
        round(pieza.x, 6),
        round(pieza.y, 6),
        round(pieza.ancho, 6),
        round(pieza.profundidad, 6),
    )

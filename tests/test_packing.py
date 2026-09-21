"""Contrato de las estrategias de patron.

Estos tests corren contra TODAS las estrategias registradas en ESTRATEGIAS.
Cuando se agregue una nueva (por ejemplo un patron alterno para el trabado),
basta con anadirla a la lista: si no respeta el contrato, se cae aqui.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from arrume.domain.models import Area
from arrume.packing import Guillotina
from invariantes import TOL, fuera_del_area, mide_la_caja, sin_solapamientos_2d

ESTRATEGIAS = [Guillotina()]

AREAS_Y_CAJAS = [
    ((120, 100), (40, 30)),
    ((120, 80), (40, 40)),
    ((120, 100), (33, 27)),
    ((100, 100), (30, 30)),
    ((110, 90), (45, 25)),
    ((120, 100), (23, 17)),
    ((120, 80), (60, 40)),
    ((120, 100), (37.5, 27.5)),
]


@pytest.fixture(params=ESTRATEGIAS, ids=lambda e: e.nombre)
def estrategia(request):
    return request.param


@pytest.mark.parametrize("medidas_area, medidas_caja", AREAS_Y_CAJAS)
def test_ninguna_pieza_se_sale_del_area(estrategia, medidas_area, medidas_caja):
    area, caja = Area(*medidas_area), Area(*medidas_caja)
    piezas = estrategia.generar(area, caja)
    assert piezas, "deberia caber al menos una caja"
    assert fuera_del_area(piezas, area) == []


@pytest.mark.parametrize("medidas_area, medidas_caja", AREAS_Y_CAJAS)
def test_ningun_par_de_piezas_se_solapa(estrategia, medidas_area, medidas_caja):
    piezas = estrategia.generar(Area(*medidas_area), Area(*medidas_caja))
    assert sin_solapamientos_2d(piezas) == []


@pytest.mark.parametrize("medidas_area, medidas_caja", AREAS_Y_CAJAS)
def test_cada_pieza_mide_la_caja(estrategia, medidas_area, medidas_caja):
    caja = Area(*medidas_caja)
    piezas = estrategia.generar(Area(*medidas_area), caja)
    assert all(mide_la_caja(pieza, caja) for pieza in piezas)


@pytest.mark.parametrize("medidas_area, medidas_caja", AREAS_Y_CAJAS)
def test_nunca_cubre_mas_del_area_disponible(estrategia, medidas_area, medidas_caja):
    area = Area(*medidas_area)
    piezas = estrategia.generar(area, Area(*medidas_caja))
    cubierto = sum(pieza.superficie for pieza in piezas)
    assert cubierto <= area.superficie + TOL


@pytest.mark.parametrize("medidas_area, medidas_caja", AREAS_Y_CAJAS)
def test_nunca_es_peor_que_el_bloque_uniforme(estrategia, medidas_area, medidas_caja):
    """El patron debe meter al menos tantas cajas como una rejilla simple."""
    ancho, profundidad = medidas_area
    cdx, cdy = medidas_caja
    rejilla = max(
        int(ancho // cdx) * int(profundidad // cdy),
        int(ancho // cdy) * int(profundidad // cdx),
    )
    piezas = estrategia.generar(Area(*medidas_area), Area(*medidas_caja))
    assert len(piezas) >= rejilla


def test_patron_optimo_cuando_la_caja_divide_exacto(estrategia):
    piezas = estrategia.generar(Area(120, 100), Area(40, 50))
    assert len(piezas) == 6  # 3 x 2, sin desperdicio


def test_sin_piezas_cuando_la_caja_no_cabe(estrategia):
    assert estrategia.generar(Area(100, 100), Area(200, 50)) == []
    assert estrategia.generar(Area(100, 100), Area(150, 150)) == []


def test_la_caja_girada_cabe_aunque_de_frente_no(estrategia):
    """Una caja de 150x50 no cabe de frente en un area de 100x200, girada si."""
    piezas = estrategia.generar(Area(100, 200), Area(150, 50))
    assert len(piezas) == 2
    assert all((p.ancho, p.profundidad) == (50, 150) for p in piezas)


@settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    ancho=st.integers(min_value=20, max_value=120),
    profundidad=st.integers(min_value=20, max_value=120),
    caja_ancho=st.integers(min_value=10, max_value=60),
    caja_profundidad=st.integers(min_value=10, max_value=60),
)
def test_propiedades_con_medidas_aleatorias(
    ancho, profundidad, caja_ancho, caja_profundidad
):
    area, caja = Area(ancho, profundidad), Area(caja_ancho, caja_profundidad)
    piezas = Guillotina().generar(area, caja)

    assert fuera_del_area(piezas, area) == []
    assert sin_solapamientos_2d(piezas) == []
    assert all(mide_la_caja(pieza, caja) for pieza in piezas)
    assert sum(p.superficie for p in piezas) <= area.superficie + TOL

"""Invariantes del arrume completo: cuentas, alturas y volumenes que no chocan."""

from __future__ import annotations

import pytest
from invariantes import TOL, fuera_del_area, sin_solapamientos_3d

from arrume import Caja, Pallet, Restricciones, construir_arrume
from arrume.domain.errors import CajaNoCabe
from arrume.stacking import area_disponible

CONFIGS = [
    ((120, 100, 15), (40, 30, 25), 5, True, 0),
    ((120, 80, 15), (40, 40, 30), 3, True, 0),
    ((120, 100, 15), (33, 27, 20), 4, False, 0),
    ((100, 100, 12), (30, 30, 30), 2, True, 5),
    ((120, 100, 15), (23, 17, 11), 6, True, 3),
    ((110, 90, 14), (37.5, 27.5, 22), 3, False, 2),
]


def _arrume(config):
    medidas_pallet, medidas_caja, niveles, trabado, vuelo = config
    return construir_arrume(
        Pallet(*medidas_pallet),
        Caja(*medidas_caja),
        Restricciones(niveles=niveles, trabado=trabado, vuelo=vuelo),
    )


@pytest.mark.parametrize("config", CONFIGS)
def test_el_total_es_las_cajas_por_nivel_por_los_niveles(config):
    arrume = _arrume(config)
    assert arrume.total_cajas == arrume.cajas_por_nivel * arrume.niveles


@pytest.mark.parametrize("config", CONFIGS)
def test_todos_los_niveles_tienen_las_mismas_cajas(config):
    arrume = _arrume(config)
    por_nivel = [
        sum(1 for c in arrume.cajas if c.nivel == n) for n in range(arrume.niveles)
    ]
    assert por_nivel == [arrume.cajas_por_nivel] * arrume.niveles


@pytest.mark.parametrize("config", CONFIGS)
def test_ninguna_caja_ocupa_el_volumen_de_otra(config):
    arrume = _arrume(config)
    assert sin_solapamientos_3d(arrume.cajas) == []


@pytest.mark.parametrize("config", CONFIGS)
def test_ninguna_caja_sobresale_mas_del_vuelo_permitido(config):
    arrume = _arrume(config)
    area = area_disponible(arrume.pallet, arrume.restricciones)
    vuelo = arrume.restricciones.vuelo
    # Se comparan en coordenadas del area (el arrume se guarda con el vuelo ya restado)
    trasladadas = [
        type(c)(c.x + vuelo, c.y + vuelo, c.z, c.ancho, c.profundidad, c.alto, c.nivel)
        for c in arrume.cajas
    ]
    assert fuera_del_area(trasladadas, area) == []


@pytest.mark.parametrize("config", CONFIGS)
def test_los_niveles_se_apoyan_uno_sobre_otro_sin_huecos(config):
    arrume = _arrume(config)
    alto_caja = arrume.caja.alto
    for caja in arrume.cajas:
        esperado = arrume.pallet.alto + caja.nivel * alto_caja
        assert abs(caja.z - esperado) < TOL
    assert max(c.z2 for c in arrume.cajas) == pytest.approx(arrume.altura_total)


@pytest.mark.parametrize("config", CONFIGS)
def test_un_nivel_nunca_cubre_mas_que_el_area_disponible(config):
    arrume = _arrume(config)
    area = area_disponible(arrume.pallet, arrume.restricciones)
    cubierto = sum(pieza.superficie for pieza in arrume.patron_base)
    assert 0 < cubierto <= area.superficie + TOL


@pytest.mark.parametrize("config", CONFIGS)
def test_sin_vuelo_el_aprovechamiento_no_pasa_del_cien(config):
    arrume = _arrume(config)
    if arrume.restricciones.vuelo:
        # Con vuelo las cajas sobresalen del pallet y el porcentaje lo supera
        assert arrume.aprovechamiento > 0
    else:
        assert 0 < arrume.aprovechamiento <= 100 + TOL


def test_un_solo_nivel_es_valido():
    arrume = construir_arrume(
        Pallet(120, 100, 15), Caja(40, 30, 25), Restricciones(niveles=1)
    )
    assert arrume.total_cajas == arrume.cajas_por_nivel
    assert arrume.altura_total == 40


def test_el_vuelo_permite_meter_mas_cajas():
    pallet, caja = Pallet(120, 100, 15), Caja(40, 30, 25)
    sin_vuelo = construir_arrume(pallet, caja, Restricciones(niveles=1, vuelo=0))
    con_vuelo = construir_arrume(pallet, caja, Restricciones(niveles=1, vuelo=10))
    assert con_vuelo.cajas_por_nivel >= sin_vuelo.cajas_por_nivel


def test_si_la_caja_no_cabe_se_lanza_un_error_del_dominio():
    with pytest.raises(CajaNoCabe) as error:
        construir_arrume(
            Pallet(120, 100, 15), Caja(200, 200, 10), Restricciones(niveles=2)
        )
    assert "200" in str(error.value)


def test_el_peso_total_sale_del_peso_de_la_caja():
    arrume = construir_arrume(
        Pallet(120, 100, 15),
        Caja(40, 30, 25),
        Restricciones(niveles=2, peso_caja=10),
    )
    assert arrume.peso_total == arrume.total_cajas * 10


def test_sin_peso_de_caja_no_hay_peso_total():
    arrume = construir_arrume(
        Pallet(120, 100, 15), Caja(40, 30, 25), Restricciones(niveles=2)
    )
    assert arrume.peso_total is None


def test_se_puede_cambiar_la_estrategia_sin_tocar_el_apilado():
    """Inversion de dependencias: el apilador acepta cualquier EstrategiaPatron."""
    from arrume.domain.models import Pieza

    class UnaSolaCaja:
        nombre = "una-sola-caja"

        def generar(self, area, caja):
            return [Pieza(0, 0, caja.ancho, caja.profundidad)]

    arrume = construir_arrume(
        Pallet(120, 100, 15),
        Caja(40, 30, 25),
        Restricciones(niveles=3),
        estrategia=UnaSolaCaja(),
    )
    assert arrume.estrategia == "una-sola-caja"
    assert arrume.cajas_por_nivel == 1
    assert arrume.total_cajas == 3

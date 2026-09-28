"""Pisos normales y cruzados sobre un acomodo de nivel propio."""

from __future__ import annotations

import pytest
from invariantes import fuera_del_area, sin_solapamientos_2d, sin_solapamientos_3d

from arrume import Caja, Pallet, Restricciones
from arrume.domain.errors import AcomodoInvalido, ConfiguracionInvalida
from arrume.domain.models import Area, Pieza
from arrume.pisos import cruzar, reparto, validar
from arrume.stacking import construir_por_pisos

PALLET = Pallet(120, 100, 15)
CAJA = Caja(40, 30, 25)

# Una fila de tres cajas derechas pegada al frente, y una girada en la esquina
A_MANO = [
    Pieza(0, 0, 40, 30),
    Pieza(40, 0, 40, 30),
    Pieza(80, 0, 40, 30),
    Pieza(0, 30, 30, 40),
]


# =====================================================================
# Reparto
# =====================================================================


@pytest.mark.parametrize("iguales, esperado", [
    (1, "NCNCNC"),
    (2, "NNCNCN"),
    (3, "NNNCNC"),
    (6, "NNNNNN"),
    (9, "NNNNNN"),
])
def test_los_primeros_normales_y_despues_se_turnan(iguales, esperado):
    pisos = reparto(6, cruzados=True, iguales=iguales)
    assert "".join(forma[0].upper() for forma in pisos) == esperado


def test_sin_cruzar_todos_normales():
    assert reparto(4, cruzados=False, iguales=2) == ["normal"] * 4


@pytest.mark.parametrize("iguales", [0, -1, 1.5, True])
def test_los_primeros_normales_son_al_menos_uno(iguales):
    with pytest.raises(ConfiguracionInvalida):
        reparto(4, iguales=iguales)


def test_un_piso_solo_puede_ser_normal_o_cruzado():
    assert validar(["normal", "cruzado"]) == ["normal", "cruzado"]
    with pytest.raises(ConfiguracionInvalida) as error:
        validar(["normal", "de lado"])
    assert "'de lado'" in str(error.value)


# =====================================================================
# Cruzar
# =====================================================================


def test_cruzar_es_media_vuelta_y_sigue_siendo_valido():
    area = Area(120, 100)
    cruzado = cruzar(A_MANO, area)
    assert (cruzado[0].x, cruzado[0].y) == (80, 70)
    assert fuera_del_area(cruzado, area) == []
    assert sin_solapamientos_2d(cruzado) == []


def test_cruzar_dos_veces_deja_el_acomodo_como_estaba():
    area = Area(120, 100)
    assert cruzar(cruzar(A_MANO, area), area) == A_MANO


# =====================================================================
# Arrume
# =====================================================================


def test_el_arrume_apila_el_acomodo_propio():
    arrume = construir_por_pisos(
        PALLET, CAJA, Restricciones(niveles=4), reparto(4), A_MANO
    )
    assert arrume.total_cajas == 4 * len(A_MANO)
    assert arrume.acomodo_de(1).piezas == tuple(A_MANO)
    assert arrume.acomodo_de(2).nombre == "cruzado"
    assert sin_solapamientos_3d(arrume.cajas) == []
    assert arrume.estrategia == "a mano"


def test_sin_acomodo_lo_calcula_el_programa():
    arrume = construir_por_pisos(PALLET, CAJA, Restricciones(niveles=2), reparto(2))
    assert arrume.cajas_por_nivel == 10


def test_solo_se_guardan_las_formas_que_se_usan():
    arrume = construir_por_pisos(
        PALLET, CAJA, Restricciones(niveles=3), ["cruzado"] * 3, A_MANO
    )
    assert [a.nombre for a in arrume.acomodos] == ["cruzado"]
    assert arrume.restricciones.trabado is False


def test_hace_falta_un_piso_por_nivel():
    with pytest.raises(ConfiguracionInvalida) as error:
        construir_por_pisos(PALLET, CAJA, Restricciones(niveles=3), ["normal"])
    assert "1 pisos indicados para 3 niveles" in str(error.value)


def test_un_acomodo_vacio_no_se_convierte_en_el_automatico():
    with pytest.raises(ConfiguracionInvalida):
        construir_por_pisos(PALLET, CAJA, Restricciones(niveles=1), ["normal"], [])


def test_un_acomodo_con_cajas_encimadas_se_rechaza():
    encimadas = [Pieza(0, 0, 40, 30), Pieza(20, 0, 40, 30)]
    with pytest.raises(AcomodoInvalido) as error:
        construir_por_pisos(
            PALLET, CAJA, Restricciones(niveles=1), ["normal"], encimadas
        )
    assert "se pisa" in str(error.value)

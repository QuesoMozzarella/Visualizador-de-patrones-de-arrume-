"""Los modelos rechazan datos imposibles en el momento de construirse."""

from __future__ import annotations

import dataclasses

import pytest

from arrume import Caja, Pallet, Restricciones
from arrume.domain.errors import ConfiguracionInvalida
from arrume.domain.models import Area, Colocacion, Pieza


def test_pallet_valido_expone_su_superficie():
    pallet = Pallet(120, 100, 15)
    assert pallet.superficie == Area(120, 100)
    assert pallet.superficie.superficie == 12000


def test_caja_valida_calcula_volumen_y_base():
    caja = Caja(40, 30, 25)
    assert caja.volumen == 30000
    assert caja.base == Area(40, 30)


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: Pallet(0, 100, 15),
        lambda: Pallet(-120, 100, 15),
        lambda: Pallet(120, 0, 15),
        lambda: Pallet(120, 100, 0),
        lambda: Pallet(float("inf"), 100, 15),
        lambda: Pallet(float("nan"), 100, 15),
        lambda: Pallet("120", 100, 15),
        lambda: Pallet(True, 100, 15),
        lambda: Caja(0, 30, 25),
        lambda: Caja(40, -30, 25),
        lambda: Caja(40, 30, 0),
        lambda: Area(0, 10),
        lambda: Pieza(0, 0, 0, 30),
        lambda: Colocacion(0, 0, 0, 40, 30, 25, -1),
        lambda: Colocacion(0, 0, 0, 40, 30, 0, 0),
    ],
)
def test_dimensiones_imposibles_se_rechazan(constructor):
    with pytest.raises(ConfiguracionInvalida):
        constructor()


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: Restricciones(niveles=0),
        lambda: Restricciones(niveles=-3),
        lambda: Restricciones(niveles=2.5),
        lambda: Restricciones(niveles=True),
        lambda: Restricciones(niveles=3, vuelo=-1),
    ],
)
def test_restricciones_imposibles_se_rechazan(constructor):
    with pytest.raises(ConfiguracionInvalida):
        constructor()


def test_restricciones_por_defecto_son_razonables():
    limites = Restricciones(niveles=5)
    assert limites.trabado is True
    assert limites.vuelo == 0


def test_los_modelos_son_inmutables():
    pallet = Pallet(120, 100, 15)
    with pytest.raises(dataclasses.FrozenInstanceError):
        pallet.ancho = 200


def test_la_pieza_calcula_sus_extremos():
    pieza = Pieza(10, 20, 40, 30)
    assert (pieza.x2, pieza.y2) == (50, 50)
    assert pieza.superficie == 1200


def test_la_colocacion_expone_el_cuerpo_para_dibujar():
    caja = Colocacion(1, 2, 3, 40, 30, 25, nivel=0)
    assert caja.cuerpo == (1, 2, 3, 40, 30, 25)
    assert (caja.x2, caja.y2, caja.z2) == (41, 32, 28)

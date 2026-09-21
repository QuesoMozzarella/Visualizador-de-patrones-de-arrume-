"""Trabazon: que el nivel alterno pise de verdad las juntas del de abajo.

El trabado existe para que el arrume no se abra. La implementacion vieja
giraba el nivel 180 grados, y eso solo traba cuando el patron base no es
simetrico: medido sobre 10 configuraciones habituales, trababa en 3.
La estrategia actual prueba varios patrones alternos y traba en 7.

Las otras 3 son teselados perfectos (el nivel llena el pallet exacto, sin
holgura): ahi no existe ninguna recolocacion que trabe, y lo que se exige
es que el informe lo diga en vez de aparentarlo.
"""

from __future__ import annotations

import pytest

from arrume import Caja, Pallet, Restricciones, construir_arrume
from arrume.domain.models import Area
from arrume.packing import Guillotina
from arrume.reporting import generar_informe
from arrume.trabazon import (
    MejorAlterno,
    Rotacion180,
    SinTrabazon,
    cajas_calcadas,
    calidad,
)
from invariantes import fuera_del_area, sin_solapamientos_2d

# Configuraciones donde el giro de 180 grados NO trababa
ANTES_NO_TRABABAN = [
    ((120, 100), (33, 27)),
    ((100, 100), (30, 30)),
    ((110, 90), (45, 25)),
    ((80, 60), (25, 20)),
]

# El nivel llena el area exacta: no hay trabazon posible
SIN_TRABAZON_POSIBLE = [
    ((120, 80), (40, 40)),
    ((120, 80), (60, 40)),
    ((120, 100), (50, 40)),
]


def _arrume(medidas_pallet, medidas_caja, **limites):
    limites.setdefault("niveles", 4)
    return construir_arrume(
        Pallet(*medidas_pallet, 15), Caja(*medidas_caja, 25), Restricciones(**limites)
    )


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


# =====================================================================
# Comportamiento del apilado
# =====================================================================


def test_sin_trabado_todos_los_niveles_son_identicos():
    arrume = _arrume((120, 100), (40, 30), trabado=False)
    huellas = _huellas_por_nivel(arrume)
    assert all(nivel == huellas[0] for nivel in huellas)
    assert arrume.trabazon == "en columna"


def test_con_trabado_los_niveles_alternan_entre_dos_patrones():
    arrume = _arrume((120, 100), (40, 30), niveles=5)
    huellas = _huellas_por_nivel(arrume)
    assert huellas[0] == huellas[2] == huellas[4]
    assert huellas[1] == huellas[3]
    assert huellas[0] != huellas[1]


@pytest.mark.parametrize("medidas_pallet, medidas_caja", ANTES_NO_TRABABAN)
def test_ahora_traba_donde_la_rotacion_no_trababa(medidas_pallet, medidas_caja):
    arrume = _arrume(medidas_pallet, medidas_caja)
    assert cajas_calcadas(arrume.patron_base, arrume.patron_alterno) == 0
    assert generar_informe(arrume).traba is True


@pytest.mark.parametrize("medidas_pallet, medidas_caja", ANTES_NO_TRABABAN)
def test_la_rotacion_sola_seguia_sin_trabar(medidas_pallet, medidas_caja):
    """Deja constancia del fallo viejo: por eso hizo falta cambiarla."""
    arrume = construir_arrume(
        Pallet(*medidas_pallet, 15),
        Caja(*medidas_caja, 25),
        Restricciones(niveles=2),
        trabazon=Rotacion180(),
    )
    calcadas = cajas_calcadas(arrume.patron_base, arrume.patron_alterno)
    assert calcadas == arrume.cajas_por_nivel


@pytest.mark.parametrize("medidas_pallet, medidas_caja", SIN_TRABAZON_POSIBLE)
def test_si_el_patron_llena_exacto_se_avisa_en_vez_de_aparentar(
    medidas_pallet, medidas_caja
):
    arrume = _arrume(medidas_pallet, medidas_caja)
    informe = generar_informe(arrume)
    assert informe.traba is False
    assert informe.cajas_calcadas == informe.cajas_por_nivel
    assert any("no hace efecto" in aviso for aviso in informe.avisos)


def test_dejar_vuelo_desbloquea_un_patron_que_no_trababa():
    sin_vuelo = _arrume((120, 80), (40, 40))
    con_vuelo = _arrume((120, 80), (40, 40), vuelo=5)
    assert generar_informe(sin_vuelo).traba is False
    assert generar_informe(con_vuelo).traba is True
    assert con_vuelo.cajas_por_nivel == sin_vuelo.cajas_por_nivel


def test_el_trabado_no_pierde_ni_una_caja():
    trabado = _arrume((120, 100), (33, 27))
    columna = _arrume((120, 100), (33, 27), trabado=False)
    assert trabado.total_cajas == columna.total_cajas


def test_con_un_solo_nivel_no_se_habla_de_trabazon():
    informe = generar_informe(_arrume((120, 100), (40, 30), niveles=1))
    assert informe.traba is False
    assert informe.avisos == ()


# =====================================================================
# El patron alterno sigue siendo un patron valido
# =====================================================================


@pytest.mark.parametrize(
    "medidas_pallet, medidas_caja", ANTES_NO_TRABABAN + SIN_TRABAZON_POSIBLE
)
def test_el_patron_alterno_cumple_el_mismo_contrato(medidas_pallet, medidas_caja):
    arrume = _arrume(medidas_pallet, medidas_caja, vuelo=0)
    area = Area(*medidas_pallet)
    assert len(arrume.patron_alterno) == len(arrume.patron_base)
    assert fuera_del_area(arrume.patron_alterno, area) == []
    assert sin_solapamientos_2d(arrume.patron_alterno) == []


def test_una_trabazon_que_pierde_cajas_se_rechaza():
    """Contrato del colaborador: todos los niveles llevan las mismas cajas."""

    class TrabazonRota:
        nombre = "rota"

        def alterno(self, base, area, caja, estrategia):
            return list(base)[:-1]

    from arrume.domain.errors import ConfiguracionInvalida

    with pytest.raises(ConfiguracionInvalida) as error:
        construir_arrume(
            Pallet(120, 100, 15),
            Caja(40, 30, 25),
            Restricciones(niveles=2),
            trabazon=TrabazonRota(),
        )
    assert "mismas cajas" in str(error.value)


# =====================================================================
# La medida de la trabazon
# =====================================================================


def test_un_nivel_calcado_mide_cero():
    base = Guillotina().generar(Area(120, 100), Area(40, 30))
    assert calidad(base, base) == 0.0
    assert cajas_calcadas(base, base) == len(base)


def test_repartir_el_apoyo_entre_dos_cajas_mide_medio():
    from arrume.domain.models import Pieza

    abajo = [Pieza(0, 0, 40, 30), Pieza(40, 0, 40, 30)]
    encima = [Pieza(20, 0, 40, 30)]  # justo sobre la junta
    assert calidad(abajo, encima) == pytest.approx(0.5)
    assert cajas_calcadas(abajo, encima) == 0


def test_la_mejor_alternativa_nunca_es_peor_que_la_rotacion():
    for medidas_pallet, medidas_caja in ANTES_NO_TRABABAN + SIN_TRABAZON_POSIBLE:
        area, caja = Area(*medidas_pallet), Area(*medidas_caja)
        base = Guillotina().generar(area, caja)
        girado = Rotacion180().alterno(base, area, caja, Guillotina())
        mejor = MejorAlterno().alterno(base, area, caja, Guillotina())
        assert calidad(base, mejor) >= calidad(base, girado)


def test_sin_trabazon_devuelve_el_mismo_patron():
    area, caja = Area(120, 100), Area(40, 30)
    base = Guillotina().generar(area, caja)
    assert SinTrabazon().alterno(base, area, caja, Guillotina()) == base

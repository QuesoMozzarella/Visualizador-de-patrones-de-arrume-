"""Acomodos por nivel: decidir que va en cada piso, y que no valga todo.

Es la base de poder acomodar un nivel a mano: el arrume deja de ser
"un patron y su alterno alternando por paridad" y pasa a ser "estos
acomodos, y este va en este nivel".
"""

from __future__ import annotations

import pytest
from invariantes import sin_solapamientos_3d

from arrume import Caja, Pallet, Restricciones
from arrume.domain.errors import AcomodoInvalido, ConfiguracionInvalida
from arrume.domain.models import Acomodo, Pieza
from arrume.packing import Guillotina
from arrume.packing.transformaciones import rotar_180
from arrume.stacking import area_disponible, construir_con_acomodos

PALLET = Pallet(120, 100, 15)
CAJA = Caja(40, 30, 25)


def _acomodos():
    """Dos acomodos validos del mismo pallet: el calculado y su giro."""
    area = area_disponible(PALLET, Restricciones(niveles=1))
    base = tuple(Guillotina().generar(area, CAJA.base))
    return (
        Acomodo("derecho", base),
        Acomodo("girado", tuple(rotar_180(list(base), area))),
    )


# =====================================================================
# El modelo
# =====================================================================


def test_un_acomodo_sin_nombre_o_sin_cajas_no_existe():
    with pytest.raises(ConfiguracionInvalida):
        Acomodo("  ", (Pieza(0, 0, 40, 30),))
    with pytest.raises(ConfiguracionInvalida):
        Acomodo("vacio", ())


def test_el_acomodo_cuenta_sus_cajas_y_su_superficie():
    acomodo = Acomodo("dos", (Pieza(0, 0, 40, 30), Pieza(40, 0, 40, 30)))
    assert acomodo.cajas == 2
    assert acomodo.superficie == 2400


def test_cada_nivel_dice_que_acomodo_lleva():
    derecho, girado = _acomodos()
    arrume = construir_con_acomodos(
        PALLET, CAJA, Restricciones(niveles=5), [derecho, girado], [0, 0, 1, 0, 1]
    )
    assert [arrume.acomodo_de(n).nombre for n in range(1, 6)] == [
        "derecho", "derecho", "girado", "derecho", "girado",
    ]


def test_pedir_un_nivel_que_no_existe_lo_dice():
    arrume = construir_con_acomodos(
        PALLET, CAJA, Restricciones(niveles=2), list(_acomodos()), [0, 1]
    )
    with pytest.raises(ConfiguracionInvalida):
        arrume.acomodo_de(3)
    with pytest.raises(ConfiguracionInvalida):
        arrume.acomodo_de(0)


# =====================================================================
# Lo que pidio el usuario: nivel 1 y 2 iguales, y del 3 intercalados
# =====================================================================


def test_los_dos_primeros_niveles_iguales_y_el_resto_intercalado():
    derecho, girado = _acomodos()
    reparto = [0, 0] + [(nivel % 2) for nivel in range(4)]  # 0,0,0,1,0,1

    arrume = construir_con_acomodos(
        PALLET, CAJA, Restricciones(niveles=6), [derecho, girado], reparto
    )

    nombres = [arrume.acomodo_de(n).nombre for n in range(1, 7)]
    assert nombres == ["derecho", "derecho", "derecho", "girado", "derecho", "girado"]
    assert arrume.acomodo_de(1).piezas == arrume.acomodo_de(2).piezas
    assert arrume.acomodo_de(3).piezas != arrume.acomodo_de(4).piezas


def test_repetir_un_acomodo_no_lo_duplica():
    derecho, girado = _acomodos()
    arrume = construir_con_acomodos(
        PALLET, CAJA, Restricciones(niveles=8), [derecho, girado], [0] * 6 + [1, 1]
    )
    assert len(arrume.acomodos) == 2
    assert arrume.total_cajas == 8 * derecho.cajas


def test_las_cajas_quedan_donde_dice_el_reparto():
    derecho, girado = _acomodos()
    arrume = construir_con_acomodos(
        PALLET, CAJA, Restricciones(niveles=3), [derecho, girado], [0, 1, 0]
    )
    huella = lambda nivel: sorted(  # noqa: E731
        (c.x, c.y, c.ancho, c.profundidad) for c in arrume.cajas if c.nivel == nivel
    )
    assert huella(0) == huella(2)
    assert huella(0) != huella(1)


# =====================================================================
# Niveles con distinto numero de cajas
# =====================================================================


def test_un_nivel_puede_llevar_menos_cajas_que_otro():
    """Al acomodar a mano se puede quitar una caja de un nivel."""
    derecho, _ = _acomodos()
    incompleto = Acomodo("con un hueco", derecho.piezas[:-1])

    arrume = construir_con_acomodos(
        PALLET, CAJA, Restricciones(niveles=3), [derecho, incompleto], [0, 1, 0]
    )

    assert arrume.cajas_de_nivel(1) == derecho.cajas
    assert arrume.cajas_de_nivel(2) == derecho.cajas - 1
    assert arrume.total_cajas == derecho.cajas * 2 + (derecho.cajas - 1)


def test_ningun_acomodo_hace_que_las_cajas_se_pisen():
    derecho, girado = _acomodos()
    arrume = construir_con_acomodos(
        PALLET, CAJA, Restricciones(niveles=4), [derecho, girado], [0, 0, 1, 1]
    )
    assert sin_solapamientos_3d(arrume.cajas) == []


# =====================================================================
# Acomodos que no se pueden usar
# =====================================================================


def test_un_acomodo_que_se_sale_del_pallet_se_rechaza():
    fuera = Acomodo("fuera", (Pieza(110, 0, 40, 30),))
    with pytest.raises(AcomodoInvalido) as error:
        construir_con_acomodos(PALLET, CAJA, Restricciones(niveles=1), [fuera], [0])
    assert "se sale" in str(error.value)


def test_un_acomodo_con_cajas_encimadas_se_rechaza():
    encimadas = Acomodo("encimadas", (Pieza(0, 0, 40, 30), Pieza(20, 0, 40, 30)))
    with pytest.raises(AcomodoInvalido) as error:
        construir_con_acomodos(PALLET, CAJA, Restricciones(niveles=1), [encimadas], [0])
    assert "se pisa" in str(error.value)


def test_una_caja_que_no_es_la_caja_del_arrume_se_rechaza():
    ajena = Acomodo("ajena", (Pieza(0, 0, 50, 50),))
    with pytest.raises(AcomodoInvalido) as error:
        construir_con_acomodos(PALLET, CAJA, Restricciones(niveles=1), [ajena], [0])
    assert "no mide 40 x 30" in str(error.value)


def test_la_caja_girada_si_vale():
    derecho, _ = _acomodos()
    girada = Acomodo("girada", (Pieza(0, 0, 30, 40),))
    arrume = construir_con_acomodos(
        PALLET, CAJA, Restricciones(niveles=1), [girada], [0]
    )
    assert arrume.total_cajas == 1


def test_el_vuelo_amplia_lo_que_se_considera_dentro():
    asomada = Acomodo("asomada", (Pieza(0, 0, 40, 30),))
    limites = Restricciones(niveles=1, vuelo=10)
    arrume = construir_con_acomodos(PALLET, CAJA, limites, [asomada], [0])
    # en coordenadas del pallet queda sobresaliendo, que es lo que permite el vuelo
    assert arrume.cajas[0].x == -10


@pytest.mark.parametrize("reparto", [[0, 5], [0, -1], [2]])
def test_un_reparto_que_apunta_a_un_acomodo_inexistente_se_rechaza(reparto):
    acomodos = list(_acomodos())
    limites = Restricciones(niveles=len(reparto))
    with pytest.raises(ConfiguracionInvalida):
        construir_con_acomodos(PALLET, CAJA, limites, acomodos, reparto)


def test_el_reparto_tiene_que_cubrir_todos_los_niveles():
    acomodos = list(_acomodos())
    with pytest.raises(ConfiguracionInvalida) as error:
        construir_con_acomodos(PALLET, CAJA, Restricciones(niveles=4), acomodos, [0, 1])
    assert "niveles" in str(error.value)


def test_sin_acomodos_no_hay_arrume():
    with pytest.raises(ConfiguracionInvalida):
        construir_con_acomodos(PALLET, CAJA, Restricciones(niveles=1), [], [])

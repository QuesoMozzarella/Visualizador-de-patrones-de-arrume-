"""El servicio de la API traduce del formulario al dominio, y nada mas.

Se prueba sin levantar ningun servidor: recibe un diccionario y devuelve
un diccionario.
"""

from __future__ import annotations

import pytest

from arrume import Caja, Pallet, Restricciones
from arrume.domain.errors import ConfiguracionInvalida
from arrume.reporting import formatear
from arrume.stacking import construir_por_pisos
from arrume_api.servicio import VALORES_INICIALES, calcular, construir, para_guardar

# Un formulario tal como llega del navegador: todo texto
FORMULARIO = {
    "pallet_ancho": "120",
    "pallet_profundidad": "100",
    "pallet_alto": "15",
    "caja_ancho": "40",
    "caja_profundidad": "30",
    "caja_alto": "25",
    "niveles": "5",
    "cruzar": "1",
    "iguales": "1",
}

# Un acomodo a mano: una fila de tres cajas derechas pegada al frente
TRES_EN_FILA = [
    {"x": 0, "y": 0, "ancho": 40, "profundidad": 30},
    {"x": 40, "y": 0, "ancho": 40, "profundidad": 30},
    {"x": 80, "y": 0, "ancho": 40, "profundidad": 30},
]


# =====================================================================
# Lo que devuelve cuando todo esta bien
# =====================================================================


def test_los_valores_iniciales_dan_un_arrume_valido():
    respuesta = calcular(VALORES_INICIALES)
    assert respuesta["ok"] is True
    assert respuesta["resumen"]["cajas_por_nivel"] == 10
    assert respuesta["resumen"]["total_cajas"] == 50
    assert respuesta["resumen"]["altura_total"] == 140
    assert respuesta["avisos"] == []


def test_un_formulario_de_texto_da_lo_mismo_que_los_valores_iniciales():
    """El navegador manda cadenas; el dominio recibe numeros."""
    por_texto = calcular(FORMULARIO)["resumen"]
    por_valores = calcular(VALORES_INICIALES)["resumen"]
    assert por_texto == por_valores


def test_el_informe_es_el_del_paquete():
    """No hay un segundo formateador: se reusa el del proyecto."""
    arrume = construir_por_pisos(
        Pallet(120, 100, 15),
        Caja(40, 30, 25),
        Restricciones(niveles=5),
        ["normal", "cruzado", "normal", "cruzado", "normal"],
    )
    assert calcular(VALORES_INICIALES)["texto"] == formatear(arrume)


def test_la_geometria_llega_lista_para_dibujar():
    respuesta = calcular(VALORES_INICIALES)
    assert respuesta["pallet"] == {"ancho": 120, "profundidad": 100, "alto": 15}
    assert len(respuesta["cajas"]) == 50
    primera = respuesta["cajas"][0]
    assert set(primera) == {"x", "y", "z", "ancho", "profundidad", "alto", "nivel"}
    assert primera["z"] == 15, "el primer piso se apoya sobre el pallet"
    assert {c["nivel"] for c in respuesta["cajas"]} == {0, 1, 2, 3, 4}


def test_acepta_la_coma_decimal():
    con_coma = calcular({**FORMULARIO, "caja_ancho": "37,5", "caja_alto": "22,5"})
    con_punto = calcular({**FORMULARIO, "caja_ancho": "37.5", "caja_alto": "22.5"})
    assert con_coma["ok"] is True
    assert con_coma["resumen"] == con_punto["resumen"]


def test_acepta_medidas_decimales():
    respuesta = calcular(
        {**FORMULARIO, "caja_ancho": "37.5", "caja_profundidad": "27.5"}
    )
    assert respuesta["ok"] is True


def test_no_hay_peso_en_la_respuesta():
    resumen = calcular(FORMULARIO)["resumen"]
    assert not any("peso" in clave for clave in resumen)


def test_no_hay_trabazon_en_la_respuesta():
    resumen = calcular(FORMULARIO)["resumen"]
    assert not any("traba" in clave or "calcad" in clave for clave in resumen)


@pytest.mark.parametrize("marcado, esperado", [
    ("1", True), ("on", True), ("true", True), ("si", True), (True, True),
    ("0", False), ("", False), ("false", False), (False, False),
])
def test_entiende_como_llega_una_casilla_marcada(marcado, esperado):
    respuesta = calcular({**FORMULARIO, "cruzar": marcado})
    assert respuesta["resumen"]["intercalado"] is esperado


def _formas(respuesta):
    return [planta["forma"] for planta in respuesta["plantas"]]


def test_cruzando_se_turnan_normal_y_cruzado():
    assert _formas(calcular(FORMULARIO)) == [
        "normal", "cruzado", "normal", "cruzado", "normal",
    ]


def test_los_dos_primeros_normales_y_luego_cruzados():
    respuesta = calcular({**FORMULARIO, "niveles": "6", "iguales": "2"})
    assert _formas(respuesta) == [
        "normal", "normal", "cruzado", "normal", "cruzado", "normal",
    ]


def test_primeros_iguales_vacio_es_uno():
    assert _formas(calcular({**FORMULARIO, "iguales": ""})) == _formas(
        calcular(FORMULARIO)
    )


def test_sin_cruzar_todos_van_normales():
    respuesta = calcular({**FORMULARIO, "cruzar": "0"})
    assert set(_formas(respuesta)) == {"normal"}
    assert respuesta["resumen"]["intercalado"] is False


@pytest.mark.parametrize("pisos", [
    ["cruzado", "normal", "normal"],
    "cruzado, normal ,normal",
])
def test_cada_piso_dice_como_va(pisos):
    respuesta = calcular({**FORMULARIO, "niveles": "3", "pisos": pisos})
    assert _formas(respuesta) == ["cruzado", "normal", "normal"]


def test_el_acomodo_a_mano_es_el_que_se_apila():
    respuesta = calcular({**FORMULARIO, "acomodo": TRES_EN_FILA})
    assert respuesta["ok"] is True
    assert respuesta["resumen"]["cajas_por_nivel"] == 3
    assert respuesta["resumen"]["total_cajas"] == 15
    assert respuesta["acomodo"] == TRES_EN_FILA


def test_el_piso_cruzado_es_el_acomodo_con_media_vuelta():
    """La fila pegada al frente queda pegada al fondo en el piso cruzado."""
    respuesta = calcular({**FORMULARIO, "acomodo": TRES_EN_FILA})
    cruzado = respuesta["plantas"][1]["cajas"]
    assert sorted((c["x"], c["y"]) for c in cruzado) == [(0, 70), (40, 70), (80, 70)]


def test_el_acomodo_tambien_llega_como_texto():
    """Asi viaja en la URL de descarga."""
    import json

    respuesta = calcular({**FORMULARIO, "acomodo": json.dumps(TRES_EN_FILA)})
    assert respuesta["resumen"]["cajas_por_nivel"] == 3


def test_sin_acomodo_el_programa_lo_calcula_y_lo_devuelve():
    respuesta = calcular(FORMULARIO)
    assert len(respuesta["acomodo"]) == 10
    assert respuesta["acomodo"] == respuesta["plantas"][0]["cajas"]


def test_el_acomodo_devuelto_es_el_normal_aunque_todo_vaya_cruzado():
    todo_cruzado = calcular(
        {**FORMULARIO, "niveles": "2", "pisos": "cruzado,cruzado"}
    )
    assert todo_cruzado["acomodo"] == calcular(FORMULARIO)["acomodo"]


def test_las_plantas_traen_las_cajas_de_cada_nivel():
    respuesta = calcular(FORMULARIO)
    assert len(respuesta["plantas"]) == 5
    caja = respuesta["plantas"][0]["cajas"][0]
    assert set(caja) == {"x", "y", "ancho", "profundidad"}
    assert respuesta["resumen"]["area_ancho"] == 120


# =====================================================================
# Lo que devuelve cuando el formulario viene mal
# =====================================================================


@pytest.mark.parametrize("cambio, fragmento", [
    ({"niveles": "0"}, "al menos 1 nivel"),
    ({"niveles": "2.5"}, "entero"),
    ({"pallet_ancho": "0"}, "ancho del pallet"),
    ({"pallet_ancho": ""}, "Falta el ancho del pallet"),
    ({"caja_alto": "veinte"}, "alto de la caja debe ser un numero"),
    ({"caja_ancho": "200", "caja_profundidad": "200"}, "cabe"),
    ({"vuelo": "-5"}, "vuelo no puede ser negativo"),
    ({"iguales": "0"}, "al menos 1"),
    ({"iguales": "1.5"}, "debe ser entero"),
    ({"pisos": "normal,normal"}, "2 pisos indicados para 5 niveles"),
    ({"pisos": "normal,de lado"}, "no 'de lado'"),
    ({"acomodo": []}, "no tiene ninguna caja"),
    ({"acomodo": "{roto"}, "mal formado"),
    ({"acomodo": [{"x": 0, "y": 0}]}, "sin medidas validas"),
    ({"acomodo": TRES_EN_FILA[:1] * 2}, "se pisa"),
    ({"acomodo": [{"x": 100, "y": 0, "ancho": 40, "profundidad": 30}]}, "se sale"),
    ({"acomodo": [{"x": 0, "y": 0, "ancho": 50, "profundidad": 30}]}, "no mide"),
])
def test_un_formulario_malo_devuelve_el_error_dentro_del_resultado(cambio, fragmento):
    """Los errores viajan como datos: la pagina los muestra donde toca."""
    respuesta = calcular({**FORMULARIO, **cambio})
    assert respuesta["ok"] is False
    assert fragmento in respuesta["error"]
    assert "cajas" not in respuesta


def test_calcular_nunca_lanza_por_datos_malos():
    for datos in ({}, {"niveles": "x"}, {"pallet_ancho": None}):
        assert calcular(datos)["ok"] is False


def test_construir_si_lanza_para_quien_quiera_atraparlo():
    """calcular() envuelve; construir() deja pasar el error del dominio."""
    with pytest.raises(ConfiguracionInvalida):
        construir({**FORMULARIO, "niveles": "0"})


# =====================================================================
# Guardar
# =====================================================================


def test_para_guardar_limpia_el_nombre_y_deja_solo_los_campos_conocidos():
    nombre, datos = para_guardar(
        {"nombre": "  Pallet de galletas  ", "datos": {**FORMULARIO, "ajeno": 1}}
    )
    assert nombre == "Pallet de galletas"
    assert "ajeno" not in datos
    assert datos["pallet_ancho"] == "120"


@pytest.mark.parametrize("cuerpo, fragmento", [
    ({"datos": FORMULARIO}, "nombre"),
    ({"nombre": "   ", "datos": FORMULARIO}, "nombre"),
    ({"nombre": "x" * 101, "datos": FORMULARIO}, "100 letras"),
    ({"nombre": "sin datos"}, "Faltan los datos"),
    ({"nombre": "malo", "datos": {**FORMULARIO, "niveles": "0"}}, "al menos 1 nivel"),
])
def test_no_se_guarda_lo_que_no_se_puede_armar(cuerpo, fragmento):
    with pytest.raises(ConfiguracionInvalida) as error:
        para_guardar(cuerpo)
    assert fragmento in str(error.value)

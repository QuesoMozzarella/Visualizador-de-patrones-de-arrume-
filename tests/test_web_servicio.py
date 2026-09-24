"""La capa de servicio traduce del formulario al dominio, y nada mas.

Se prueba sin levantar ningun servidor: recibe un diccionario y devuelve
un diccionario.
"""

from __future__ import annotations

import pytest

from arrume import Caja, Pallet, Restricciones, construir_arrume
from arrume.domain.errors import ArrumeError, ConfiguracionInvalida
from arrume.reporting import formatear
from arrume.web.servicio import VALORES_INICIALES, calcular, construir, exportar

# Un formulario tal como llega del navegador: todo texto
FORMULARIO = {
    "pallet_ancho": "120",
    "pallet_profundidad": "100",
    "pallet_alto": "15",
    "caja_ancho": "40",
    "caja_profundidad": "30",
    "caja_alto": "25",
    "niveles": "5",
    "vuelo": "",
    "trabado": "1",
    "trabazon": "mejor",
    "altura_max": "",
    "peso_caja": "",
    "peso_max": "",
}


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


def test_el_informe_es_el_mismo_que_usa_la_linea_de_comandos():
    """No hay un segundo formateador: se reusa el del proyecto."""
    arrume = construir_arrume(
        Pallet(120, 100, 15), Caja(40, 30, 25), Restricciones(niveles=5)
    )
    assert calcular(VALORES_INICIALES)["texto"] == formatear(arrume)


def test_la_figura_llega_lista_para_dibujar():
    figura = calcular(VALORES_INICIALES)["figura"]
    assert "data" in figura and "layout" in figura
    # pallet + aristas del pallet + un trazo por nivel + aristas de las cajas
    assert len(figura["data"]) == 5 + 3


def test_acepta_medidas_decimales():
    respuesta = calcular(
        {**FORMULARIO, "caja_ancho": "37.5", "caja_profundidad": "27.5"}
    )
    assert respuesta["ok"] is True


def test_los_campos_vacios_son_limites_sin_poner():
    respuesta = calcular(FORMULARIO)
    assert respuesta["resumen"]["peso_total"] is None
    assert respuesta["avisos"] == []


def test_el_peso_llega_cuando_se_indica():
    respuesta = calcular({**FORMULARIO, "peso_caja": "12.5"})
    assert respuesta["resumen"]["peso_total"] == 625.0


def test_avisa_cuando_se_pasa_de_los_limites():
    respuesta = calcular({**FORMULARIO, "altura_max": "100"})
    assert len(respuesta["avisos"]) == 1
    assert "altura maxima" in respuesta["avisos"][0]


def test_avisa_cuando_el_trabado_no_hace_efecto():
    respuesta = calcular(
        {**FORMULARIO, "pallet_profundidad": "80", "caja_profundidad": "40"}
    )
    assert respuesta["resumen"]["traba"] is False
    assert any("no hace efecto" in aviso for aviso in respuesta["avisos"])


@pytest.mark.parametrize("marcado, esperado", [
    ("1", True), ("on", True), ("true", True), ("si", True), (True, True),
    ("0", False), ("", False), ("false", False), (False, False),
])
def test_entiende_como_llega_una_casilla_marcada(marcado, esperado):
    respuesta = calcular({**FORMULARIO, "trabado": marcado})
    assert respuesta["resumen"]["trabado"] is esperado


def test_se_puede_pedir_la_trabazon_vieja():
    respuesta = calcular({**FORMULARIO, "trabazon": "rotacion"})
    assert respuesta["resumen"]["trabazon"] == "rotacion 180"


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
    ({"peso_max": "500"}, "peso de la caja"),
    ({"trabazon": "inventada"}, "Trabazon desconocida"),
])
def test_un_formulario_malo_devuelve_el_error_dentro_del_resultado(cambio, fragmento):
    """Los errores viajan como datos: la pagina los muestra donde toca."""
    respuesta = calcular({**FORMULARIO, **cambio})
    assert respuesta["ok"] is False
    assert fragmento in respuesta["error"]
    assert "figura" not in respuesta


def test_calcular_nunca_lanza_por_datos_malos():
    for datos in ({}, {"niveles": "x"}, {"pallet_ancho": None}):
        assert calcular(datos)["ok"] is False


def test_construir_si_lanza_para_quien_quiera_atraparlo():
    """calcular() envuelve; construir() deja pasar el error del dominio."""
    with pytest.raises(ConfiguracionInvalida):
        construir({**FORMULARIO, "niveles": "0"})


# =====================================================================
# Descarga
# =====================================================================


def test_exportar_da_un_html_que_se_abre_sin_internet():
    contenido = exportar(FORMULARIO)
    texto = contenido.decode("utf-8")
    assert texto.lstrip().startswith("<html>") or "<html" in texto[:200]
    assert 'src="https://cdn.plot.ly' not in texto
    assert len(contenido) > 1_000_000


def test_exportar_lanza_si_el_formulario_no_sirve():
    with pytest.raises(ArrumeError):
        exportar({**FORMULARIO, "niveles": "0"})

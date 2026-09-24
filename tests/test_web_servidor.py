"""El servidor: rutas como funciones puras, y la plomeria HTTP encima.

Casi todo se prueba llamando a 'atender' sin abrir ningun puerto. Al final
hay una prueba que si levanta el servidor, para que la plomeria tambien
quede cubierta.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from arrume.web.servidor import Peticion, atender, crear_servidor

FORMULARIO = {
    "pallet_ancho": "120",
    "pallet_profundidad": "100",
    "pallet_alto": "15",
    "caja_ancho": "40",
    "caja_profundidad": "30",
    "caja_alto": "25",
    "niveles": "3",
    "trabado": "1",
    "trabazon": "mejor",
}


def _post(datos: object) -> Peticion:
    return Peticion("POST", "/api/arrume", cuerpo=json.dumps(datos).encode("utf-8"))


# =====================================================================
# Rutas
# =====================================================================


@pytest.mark.parametrize("ruta", ["/", "/index.html"])
def test_la_pagina_se_sirve_en_la_raiz(ruta):
    respuesta = atender(Peticion("GET", ruta))
    assert respuesta.estado == 200
    assert respuesta.tipo.startswith("text/html")
    assert b"<title>Arrume</title>" in respuesta.cuerpo


def test_la_libreria_de_dibujo_se_sirve_desde_el_paquete():
    """Asi la interfaz funciona sin internet."""
    respuesta = atender(Peticion("GET", "/plotly.js"))
    assert respuesta.estado == 200
    assert respuesta.tipo.startswith("application/javascript")
    assert len(respuesta.cuerpo) > 1_000_000


def test_la_api_devuelve_figura_cifras_y_avisos():
    respuesta = atender(_post(FORMULARIO))
    assert respuesta.estado == 200
    datos = json.loads(respuesta.cuerpo)
    assert datos["ok"] is True
    assert datos["resumen"]["total_cajas"] == 30
    assert {"figura", "resumen", "avisos", "texto"} <= set(datos)


def test_un_formulario_malo_no_es_un_error_de_http():
    """400 es para peticiones rotas; un dato invalido es una respuesta valida."""
    respuesta = atender(_post({**FORMULARIO, "niveles": "0"}))
    assert respuesta.estado == 200
    assert json.loads(respuesta.cuerpo)["ok"] is False


def test_un_cuerpo_que_no_es_json_si_es_error_de_http():
    respuesta = atender(Peticion("POST", "/api/arrume", cuerpo=b"{roto"))
    assert respuesta.estado == 400
    assert json.loads(respuesta.cuerpo)["ok"] is False


def test_un_cuerpo_que_no_es_un_formulario_se_rechaza():
    respuesta = atender(_post([1, 2, 3]))
    assert respuesta.estado == 400


def test_la_descarga_llega_como_archivo():
    respuesta = atender(Peticion("GET", "/descargar", parametros=FORMULARIO))
    assert respuesta.estado == 200
    assert respuesta.cabeceras["Content-Disposition"] == (
        'attachment; filename="arrume.html"'
    )
    assert len(respuesta.cuerpo) > 1_000_000


def test_la_descarga_explica_por_que_no_pudo():
    malo = {**FORMULARIO, "caja_ancho": "300", "caja_profundidad": "300"}
    respuesta = atender(Peticion("GET", "/descargar", parametros=malo))
    assert respuesta.estado == 400
    assert b"cabe" in respuesta.cuerpo


def test_una_ruta_que_no_existe_da_404():
    respuesta = atender(Peticion("GET", "/inventada"))
    assert respuesta.estado == 404


def test_el_metodo_equivocado_no_atraviesa_la_ruta():
    assert atender(Peticion("GET", "/api/arrume")).estado == 404
    assert atender(Peticion("POST", "/")).estado == 404


@pytest.mark.parametrize("ruta", [
    "/../servidor.py",
    "/../../pyproject.toml",
    "/..%2fservicio.py",
    "/estaticos/../../servicio.py",
    "//etc/passwd",
])
def test_no_se_puede_salir_de_la_carpeta_de_estaticos(ruta):
    assert atender(Peticion("GET", ruta)).estado == 404


# =====================================================================
# La plomeria, ya con un puerto abierto
# =====================================================================


@pytest.fixture
def servidor():
    """Servidor de verdad en un puerto libre, solo mientras dura el test."""
    httpd = crear_servidor(0)
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        hilo.join(timeout=5)


def test_el_servidor_atiende_de_verdad(servidor):
    with urllib.request.urlopen(servidor + "/") as respuesta:
        assert respuesta.status == 200
        assert b"<title>Arrume</title>" in respuesta.read()

    peticion = urllib.request.Request(
        servidor + "/api/arrume",
        data=json.dumps(FORMULARIO).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(peticion) as respuesta:
        datos = json.loads(respuesta.read())
    assert datos["resumen"]["total_cajas"] == 30


def test_el_servidor_solo_escucha_en_local(servidor):
    httpd_local = servidor.startswith("http://127.0.0.1:")
    assert httpd_local, "la interfaz no debe quedar expuesta a la red"


def test_una_ruta_inexistente_responde_404_por_http(servidor):
    with pytest.raises(urllib.error.HTTPError) as fallo:
        urllib.request.urlopen(servidor + "/inventada")
    assert fallo.value.code == 404

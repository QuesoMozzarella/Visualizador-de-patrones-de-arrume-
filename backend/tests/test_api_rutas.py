"""La API por HTTP, con el cliente de pruebas de Flask y una base temporal."""

from __future__ import annotations

import pytest

from arrume_api import create_app
from arrume_api.repositorio import RepositorioArrumes, RepositorioSqlite

FORMULARIO = {
    "pallet_ancho": 120,
    "pallet_profundidad": 100,
    "pallet_alto": 15,
    "caja_ancho": 40,
    "caja_profundidad": 30,
    "caja_alto": 25,
    "niveles": 3,
    "cruzar": True,
    "iguales": 1,
}


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "BASE_DE_DATOS": str(tmp_path / "prueba.sqlite3"),
            "FRONTEND": str(tmp_path / "sin-frontend"),
            "ORIGENES_PERMITIDOS": ["http://localhost:5173"],
        }
    )


@pytest.fixture
def cliente(app):
    return app.test_client()


# =====================================================================
# Calcular
# =====================================================================


def test_calcular_devuelve_cifras_y_geometria(cliente):
    respuesta = cliente.post("/api/calcular", json=FORMULARIO)
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["ok"] is True
    assert datos["resumen"]["total_cajas"] == 30
    assert {"cajas", "pallet", "plantas", "acomodo", "avisos", "texto"} <= set(datos)


def test_un_dato_invalido_no_es_un_error_de_http(cliente):
    respuesta = cliente.post("/api/calcular", json={**FORMULARIO, "niveles": 0})
    assert respuesta.status_code == 200
    assert respuesta.get_json()["ok"] is False


@pytest.mark.parametrize("cuerpo", [b"{roto", b"[1, 2]"])
def test_un_cuerpo_que_no_es_un_objeto_json_si_es_error(cliente, cuerpo):
    respuesta = cliente.post(
        "/api/calcular", data=cuerpo, content_type="application/json"
    )
    assert respuesta.status_code == 400
    assert "error" in respuesta.get_json()


def test_los_valores_iniciales_salen_del_backend(cliente):
    datos = cliente.get("/api/valores-iniciales").get_json()
    assert datos["pallet_ancho"] == 120
    assert datos["cruzar"] is True


# =====================================================================
# Arrumes guardados
# =====================================================================


def _guardar(cliente, nombre="Galletas", datos=None):
    return cliente.post(
        "/api/arrumes", json={"nombre": nombre, "datos": datos or FORMULARIO}
    )


def test_guardar_y_volver_a_abrir(cliente):
    creado = _guardar(cliente)
    assert creado.status_code == 201
    id = creado.get_json()["id"]

    abierto = cliente.get(f"/api/arrumes/{id}").get_json()
    assert abierto["nombre"] == "Galletas"
    assert abierto["datos"] == FORMULARIO
    assert abierto["creado"] and abierto["actualizado"]


def test_se_guarda_el_acomodo_a_mano_y_los_pisos(cliente):
    datos = {
        **FORMULARIO,
        "pisos": ["normal", "normal", "cruzado"],
        "acomodo": [{"x": 0, "y": 0, "ancho": 40, "profundidad": 30}],
    }
    id = _guardar(cliente, datos=datos).get_json()["id"]
    abierto = cliente.get(f"/api/arrumes/{id}").get_json()["datos"]
    assert abierto["pisos"] == ["normal", "normal", "cruzado"]

    # Lo guardado se vuelve a calcular tal cual
    calculado = cliente.post("/api/calcular", json=abierto).get_json()
    assert calculado["resumen"]["total_cajas"] == 3


def test_la_lista_no_trae_los_datos_y_va_del_mas_reciente(cliente):
    _guardar(cliente, "Primero")
    _guardar(cliente, "Segundo")
    lista = cliente.get("/api/arrumes").get_json()
    assert [a["nombre"] for a in lista] == ["Segundo", "Primero"]
    assert "datos" not in lista[0]


def test_actualizar_reemplaza_nombre_y_datos(cliente):
    id = _guardar(cliente).get_json()["id"]
    respuesta = cliente.put(
        f"/api/arrumes/{id}",
        json={"nombre": "Galletas grandes", "datos": {**FORMULARIO, "niveles": 6}},
    )
    assert respuesta.status_code == 200
    abierto = cliente.get(f"/api/arrumes/{id}").get_json()
    assert abierto["nombre"] == "Galletas grandes"
    assert abierto["datos"]["niveles"] == 6


def test_borrar(cliente):
    id = _guardar(cliente).get_json()["id"]
    assert cliente.delete(f"/api/arrumes/{id}").status_code == 204
    assert cliente.get(f"/api/arrumes/{id}").status_code == 404
    assert cliente.delete(f"/api/arrumes/{id}").status_code == 404


def test_no_se_guarda_un_arrume_que_no_se_puede_armar(cliente):
    respuesta = _guardar(cliente, datos={**FORMULARIO, "caja_ancho": 500})
    assert respuesta.status_code == 422
    assert "cabe" in respuesta.get_json()["error"]
    assert cliente.get("/api/arrumes").get_json() == []


def test_sin_nombre_no_se_guarda(cliente):
    respuesta = _guardar(cliente, nombre="  ")
    assert respuesta.status_code == 422
    assert "nombre" in respuesta.get_json()["error"]


@pytest.mark.parametrize("metodo, ruta", [
    ("get", "/api/arrumes/999"),
    ("put", "/api/arrumes/999"),
    ("delete", "/api/arrumes/999"),
])
def test_un_arrume_que_no_existe_da_404(cliente, metodo, ruta):
    kwargs = {"json": {"nombre": "x", "datos": FORMULARIO}} if metodo == "put" else {}
    respuesta = getattr(cliente, metodo)(ruta, **kwargs)
    assert respuesta.status_code == 404
    assert "999" in respuesta.get_json()["error"]


def test_lo_guardado_sobrevive_a_reiniciar_la_app(tmp_path):
    configuracion = {
        "TESTING": True,
        "BASE_DE_DATOS": str(tmp_path / "persiste.sqlite3"),
        "FRONTEND": str(tmp_path / "nada"),
    }
    _guardar(create_app(configuracion).test_client(), "Persistente")
    lista = create_app(configuracion).test_client().get("/api/arrumes").get_json()
    assert [a["nombre"] for a in lista] == ["Persistente"]


# =====================================================================
# Lo que no es la API
# =====================================================================


def test_una_ruta_de_la_api_que_no_existe_responde_json(cliente):
    respuesta = cliente.get("/api/inventada")
    assert respuesta.status_code == 404
    assert "error" in respuesta.get_json()


def test_el_metodo_equivocado_responde_json(cliente):
    respuesta = cliente.get("/api/calcular")
    assert respuesta.status_code == 405
    assert "error" in respuesta.get_json()


def test_cors_solo_para_los_origenes_permitidos(cliente):
    permitido = cliente.get(
        "/api/valores-iniciales", headers={"Origin": "http://localhost:5173"}
    )
    ajeno = cliente.get(
        "/api/valores-iniciales", headers={"Origin": "http://otro.example"}
    )
    assert permitido.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert "Access-Control-Allow-Origin" not in ajeno.headers


def test_sirve_el_build_de_react_si_existe(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<div id=raiz></div>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    cliente = create_app(
        {"BASE_DE_DATOS": str(tmp_path / "bd.sqlite3"), "FRONTEND": str(dist)}
    ).test_client()

    assert b"raiz" in cliente.get("/").data
    assert b"console.log" in cliente.get("/assets/app.js").data
    # Las rutas de React caen en index.html; las de la API no
    assert b"raiz" in cliente.get("/guardados/3").data
    assert cliente.get("/api/nada").status_code == 404


def test_el_repositorio_cumple_el_protocolo(tmp_path):
    assert isinstance(RepositorioSqlite(tmp_path / "r.sqlite3"), RepositorioArrumes)

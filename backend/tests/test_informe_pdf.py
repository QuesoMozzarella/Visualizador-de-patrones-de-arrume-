"""El informe en PDF: que sale, que lleva y que rechaza."""

from __future__ import annotations

import base64
import io

import pytest
from PIL import Image as ImagenPIL

from arrume import Caja, Pallet, Restricciones
from arrume.domain.errors import ConfiguracionInvalida
from arrume.pisos import reparto
from arrume.stacking import construir_por_pisos
from arrume_api import create_app
from arrume_api.informe_pdf import informe_pdf
from arrume_api.servicio import VALORES_INICIALES, informe

PALLET = Pallet(120, 100, 15)
CAJA = Caja(40, 30, 25)


def _arrume(pisos):
    return construir_por_pisos(PALLET, CAJA, Restricciones(niveles=len(pisos)), pisos)


def _png(ancho=40, alto=30) -> bytes:
    salida = io.BytesIO()
    ImagenPIL.new("RGB", (ancho, alto), "white").save(salida, format="PNG")
    return salida.getvalue()


def _data_url(imagen: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(imagen).decode()


# =====================================================================
# Contenido
# =====================================================================


def test_es_un_pdf():
    pdf = informe_pdf(_arrume(reparto(5)))
    assert pdf.startswith(b"%PDF")
    assert pdf.rstrip().endswith(b"%%EOF")


def test_lleva_cada_piso_y_como_va():
    # Sin comprimir, el texto se puede buscar en los bytes
    pdf = informe_pdf(_arrume(reparto(6, iguales=2)), comprimir=False)
    for nivel in range(1, 7):
        assert f"Piso {nivel}".encode() in pdf
    assert b"Cruzado" in pdf
    assert b"Van cruzados los pisos 3 y 5." in pdf


def test_sin_cruzar_lo_dice_y_no_dibuja_el_cruzado():
    pdf = informe_pdf(_arrume(reparto(3, cruzados=False)), comprimir=False)
    assert b"Todos los pisos van normales." in pdf
    assert b"media vuelta" not in pdf


def test_lleva_el_nombre_y_escapa_lo_que_parezca_una_etiqueta():
    pdf = informe_pdf(_arrume(reparto(2)), nombre="Pallet <b>raro</b> & cia",
                      comprimir=False)
    assert b"&lt;b&gt;" not in pdf  # se ve el texto, no la entidad
    assert b"raro" in pdf


def test_la_imagen_del_3d_va_dentro():
    sin = informe_pdf(_arrume(reparto(2)))
    con = informe_pdf(_arrume(reparto(2)), imagen_3d=_png(400, 300))
    assert b"/Subtype /Image" in con
    assert b"/Subtype /Image" not in sin


def test_los_modelos_de_caja_y_pallet_van_con_sus_medidas():
    pdf = informe_pdf(
        _arrume(reparto(2)),
        imagen_caja=_png(300, 300),
        imagen_pallet=_png(400, 300),
        comprimir=False,
    )
    assert pdf.count(b"/Subtype /Image") == 2
    assert b"Modelos 3D" in pdf
    assert b"Caja" in pdf and b"Pallet" in pdf


def test_no_habla_de_trabazon_ni_de_juntas():
    pdf = informe_pdf(_arrume(reparto(6, iguales=2)), comprimir=False)
    assert b"Trabaz" not in pdf
    assert b"calcad" not in pdf
    assert b"juntas" not in pdf


def test_muchos_pisos_ocupan_varias_paginas():
    pdf = informe_pdf(_arrume(reparto(40)), comprimir=False)
    assert b"Piso 40" in pdf and b"Piso 1" in pdf
    assert b"gina 3" in pdf  # "Pagina 3", con la tilde codificada aparte


# =====================================================================
# Servicio
# =====================================================================


def test_el_servicio_arma_el_pdf_desde_el_formulario():
    pdf, archivo = informe(
        {"datos": VALORES_INICIALES, "nombre": "Galletas 40×30 – Línea 2"}
    )
    assert pdf.startswith(b"%PDF")
    assert archivo == "arrume-galletas-40x30-linea-2.pdf"


def test_sin_nombre_el_archivo_es_arrume_pdf():
    assert informe({"datos": VALORES_INICIALES})[1] == "arrume.pdf"


def test_el_informe_usa_el_acomodo_a_mano():
    datos = {
        **VALORES_INICIALES,
        "niveles": 2,
        "acomodo": [{"x": 0, "y": 0, "ancho": 40, "profundidad": 30}],
    }
    pdf, _ = informe({"datos": datos})
    assert pdf.startswith(b"%PDF")


@pytest.mark.parametrize("imagen, fragmento", [
    ("data:image/jpeg;base64,AAAA", "PNG"),
    ("no es una imagen", "PNG"),
    ("data:image/png;base64,@@@", "mal formada"),
    (_data_url(b"GIF89a" + b"0" * 20), "PNG"),
])
@pytest.mark.parametrize("campo, cual", [
    ("imagen_3d", "del 3D"),
    ("imagen_caja", "de la caja"),
    ("imagen_pallet", "del pallet"),
])
def test_rechaza_una_imagen_que_no_es_png(imagen, fragmento, campo, cual):
    with pytest.raises(ConfiguracionInvalida) as error:
        informe({"datos": VALORES_INICIALES, campo: imagen})
    assert fragmento in str(error.value)
    assert cual in str(error.value)


def test_rechaza_datos_que_no_arman_un_arrume():
    with pytest.raises(ConfiguracionInvalida):
        informe({"datos": {**VALORES_INICIALES, "niveles": 0}})
    with pytest.raises(ConfiguracionInvalida):
        informe({"nombre": "sin datos"})


# =====================================================================
# Ruta
# =====================================================================


@pytest.fixture
def cliente(tmp_path):
    return create_app(
        {"BASE_DE_DATOS": str(tmp_path / "bd.sqlite3"), "FRONTEND": str(tmp_path)}
    ).test_client()


def test_la_ruta_devuelve_el_pdf_para_descargar(cliente):
    respuesta = cliente.post(
        "/api/informe",
        json={
            "datos": VALORES_INICIALES,
            "nombre": "Galletas",
            "imagen_3d": _data_url(_png()),
            "imagen_caja": _data_url(_png()),
            "imagen_pallet": _data_url(_png()),
        },
    )
    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/pdf"
    assert respuesta.headers["Content-Disposition"] == (
        'attachment; filename="arrume-galletas.pdf"'
    )
    assert respuesta.data.startswith(b"%PDF")


def test_la_ruta_explica_por_que_no_pudo(cliente):
    respuesta = cliente.post(
        "/api/informe", json={"datos": {**VALORES_INICIALES, "caja_ancho": 500}}
    )
    assert respuesta.status_code == 422
    assert "cabe" in respuesta.get_json()["error"]


def test_la_ruta_pide_un_objeto_json(cliente):
    respuesta = cliente.post(
        "/api/informe", data=b"[]", content_type="application/json"
    )
    assert respuesta.status_code == 400

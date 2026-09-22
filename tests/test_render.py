"""La capa de dibujo cumple sus contratos y no se mete en el dominio."""

from __future__ import annotations

import pytest

from arrume import Caja, Pallet, Restricciones, construir_arrume
from arrume.render import Exportador, Renderer
from arrume.render.plotly3d import ExportadorHTML, Plotly3D


@pytest.fixture
def arrume():
    return construir_arrume(
        Pallet(120, 100, 15), Caja(40, 30, 25), Restricciones(niveles=3)
    )


def test_el_renderer_cumple_el_protocolo():
    assert isinstance(Plotly3D(), Renderer)


def test_el_exportador_cumple_el_protocolo():
    assert isinstance(ExportadorHTML(), Exportador)


def test_la_figura_lleva_un_trazo_por_nivel(arrume):
    figura = Plotly3D().render(arrume)
    # pallet + aristas del pallet + un trazo por nivel + aristas de las cajas
    assert len(figura.data) == arrume.niveles + 3


def test_cada_nivel_se_dibuja_de_otro_color(arrume):
    figura = Plotly3D().render(arrume)
    colores = [t.color for t in figura.data if getattr(t, "color", None)]
    assert len(set(colores)) == len(colores)


def test_se_puede_cambiar_la_paleta(arrume):
    figura = Plotly3D(paleta=["#000000"]).render(arrume)
    colores = [t.color for t in figura.data if t.name and t.name.startswith("Nivel")]
    assert set(colores) == {"#000000"}


def test_el_html_por_cdn_pesa_poco(tmp_path, arrume):
    destino = tmp_path / "cdn.html"
    figura = Plotly3D().render(arrume)

    ruta = ExportadorHTML("cdn").exportar(figura, str(destino))

    assert ruta == str(destino)
    contenido = destino.read_text(encoding="utf-8")
    assert 'src="https://cdn.plot.ly' in contenido
    assert destino.stat().st_size < 500_000


def test_el_html_completo_no_necesita_internet(tmp_path, arrume):
    destino = tmp_path / "completo.html"
    figura = Plotly3D().render(arrume)

    ExportadorHTML("completo").exportar(figura, str(destino))

    contenido = destino.read_text(encoding="utf-8")
    # La libreria va dentro del archivo: no queda ningun <script src=...>
    assert 'src="https://cdn.plot.ly' not in contenido
    assert destino.stat().st_size > 1_000_000


def test_el_modo_por_defecto_es_el_liviano():
    assert ExportadorHTML().modo == "cdn"


def test_un_modo_de_html_desconocido_se_rechaza():
    with pytest.raises(ValueError) as error:
        ExportadorHTML("comprimido")
    assert "cdn" in str(error.value)


def test_el_dibujo_no_toca_el_arrume(arrume):
    antes = (arrume.cajas, arrume.patron_base, arrume.patron_alterno)
    Plotly3D().render(arrume)
    assert (arrume.cajas, arrume.patron_base, arrume.patron_alterno) == antes

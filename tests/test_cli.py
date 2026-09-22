"""La CLI traduce errores del dominio a mensajes y codigos de salida."""

from __future__ import annotations

import pytest

from arrume.cli import main


def test_el_informe_sale_por_stdout_y_termina_bien(capsys):
    assert main(["--sin-grafico"]) == 0
    salida = capsys.readouterr()
    assert "Total de cajas ...... 50" in salida.out
    assert salida.err == ""


def test_las_opciones_reemplazan_a_las_constantes_globales(capsys):
    assert main(["--sin-grafico", "--pallet", "120", "80", "--caja", "40", "40", "30",
                 "--niveles", "3"]) == 0
    salida = capsys.readouterr().out
    assert "Pallet .............. 120 x 80 x 15 cm" in salida
    assert "Caja ................ 40 x 40 x 30 cm" in salida
    assert "Total de cajas ...... 18" in salida


@pytest.mark.parametrize(
    "argumentos, fragmento",
    [
        (["--niveles", "0"], "al menos 1 nivel"),
        (["--pallet", "0", "100"], "ancho del pallet"),
        (["--caja", "200", "200", "10"], "cabe"),
        (["--vuelo", "-3"], "vuelo"),
        (["--peso-max", "500"], "peso de la caja"),
    ],
)
def test_los_errores_del_dominio_dan_codigo_2(argumentos, fragmento, capsys):
    assert main(["--sin-grafico"] + argumentos) == 2
    salida = capsys.readouterr()
    assert fragmento in salida.err
    assert salida.out == "", "un error no debe imprimir un informe a medias"


def test_sin_trabado_apila_en_columna(capsys):
    assert main(["--sin-grafico", "--sin-trabado"]) == 0
    assert "(en columna)" in capsys.readouterr().out


def test_un_argumento_que_no_es_numero_lo_rechaza_argparse():
    with pytest.raises(SystemExit) as salida:
        main(["--niveles", "muchos"])
    assert salida.value.code == 2


def test_el_grafico_se_escribe_donde_se_pide(tmp_path, capsys):
    destino = tmp_path / "salida.html"
    assert main(["--salida", str(destino), "--no-abrir"]) == 0
    assert destino.exists()
    assert destino.stat().st_size > 1000
    assert "Grafico guardado en" in capsys.readouterr().out


def test_sin_grafico_no_escribe_ningun_archivo(tmp_path, capsys):
    destino = tmp_path / "no-deberia-existir.html"
    assert main(["--sin-grafico", "--salida", str(destino)]) == 0
    assert not destino.exists()


def test_se_puede_pedir_la_trabazon_vieja(capsys):
    assert main(["--sin-grafico", "--pallet", "120", "100", "--caja", "33", "27", "20",
                 "--trabazon", "rotacion"]) == 0
    salida = capsys.readouterr().out
    assert "rotacion 180" in salida
    assert "12 de 12 cajas calcadas" in salida


def test_por_defecto_usa_la_trabazon_que_mas_traba(capsys):
    assert main(["--sin-grafico", "--pallet", "120", "100", "--caja", "33", "27", "20"]) == 0
    salida = capsys.readouterr().out
    assert "mejor alterno" in salida
    assert "0 de 12 cajas calcadas" in salida


def test_el_html_se_genera_liviano_por_defecto(tmp_path, capsys):
    destino = tmp_path / "salida.html"
    assert main(["--salida", str(destino), "--no-abrir"]) == 0
    assert destino.stat().st_size < 500_000
    assert "carga la libreria por internet" in capsys.readouterr().out


def test_se_puede_pedir_el_html_autocontenido(tmp_path, capsys):
    destino = tmp_path / "completo.html"
    assert main(["--salida", str(destino), "--no-abrir", "--html", "completo"]) == 0
    assert destino.stat().st_size > 1_000_000
    assert "carga la libreria por internet" not in capsys.readouterr().out

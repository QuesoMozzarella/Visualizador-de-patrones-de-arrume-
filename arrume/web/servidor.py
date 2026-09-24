"""Servidor local de la interfaz grafica.

Adaptador HTTP y nada mas: traduce peticiones a llamadas de arrume.web.servicio
y vuelve. Usa la libreria estandar para no obligar a instalar un framework,
pero no ata a ninguno:

  - las rutas son funciones puras Peticion -> Respuesta, reunidas en RUTAS,
    asi que montarlas sobre Flask, FastAPI o lo que sea es mapear un
    diccionario (y se pueden probar sin abrir ningun puerto),
  - la pagina es un archivo estatico cualquiera dentro de 'estaticos/', asi
    que sustituirla por el build de un React o un Vue es copiar su carpeta.

Escucha solo en 127.0.0.1: es una aplicacion de escritorio que usa el
navegador de pantalla, no un servidor expuesto a la red.
"""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..domain.errors import ArrumeError
from .servicio import calcular, exportar

ESTATICOS = (Path(__file__).parent / "estaticos").resolve()

_TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".map": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}


@dataclass(frozen=True)
class Peticion:
    """Lo que hace falta de una peticion, sin depender de como llego."""

    metodo: str
    ruta: str
    parametros: dict[str, str] = field(default_factory=dict)
    cuerpo: bytes = b""


@dataclass(frozen=True)
class Respuesta:
    """Lo que hay que devolver, sin depender de por donde se envie."""

    estado: int
    tipo: str
    cuerpo: bytes
    cabeceras: dict[str, str] = field(default_factory=dict)


def _texto(mensaje: str, estado: int = 200) -> Respuesta:
    return Respuesta(estado, "text/plain; charset=utf-8", mensaje.encode("utf-8"))


def _json(datos: object, estado: int = 200) -> Respuesta:
    cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
    return Respuesta(estado, "application/json; charset=utf-8", cuerpo)


# =====================================================================
# Rutas
# =====================================================================


def pagina(peticion: Peticion) -> Respuesta:
    """La interfaz."""
    indice = ESTATICOS / "index.html"
    if not indice.is_file():
        return _texto(f"Falta la pagina: {indice}", 500)
    return Respuesta(200, _TIPOS[".html"], indice.read_bytes())


_plotlyjs_guardado: bytes | None = None


def plotlyjs(peticion: Peticion) -> Respuesta:
    """La libreria de dibujo, servida desde el paquete instalado.

    Asi la interfaz funciona sin internet y la version siempre concuerda
    con la que genero la figura.
    """
    global _plotlyjs_guardado
    if _plotlyjs_guardado is None:
        from plotly.offline import get_plotlyjs

        _plotlyjs_guardado = get_plotlyjs().encode("utf-8")
    return Respuesta(
        200,
        _TIPOS[".js"],
        _plotlyjs_guardado,
        {"Cache-Control": "max-age=86400"},
    )


def api_arrume(peticion: Peticion) -> Respuesta:
    """Recibe el formulario y devuelve figura, cifras y avisos."""
    try:
        datos = json.loads(peticion.cuerpo or b"{}")
    except json.JSONDecodeError:
        return _json({"ok": False, "error": "El formulario llego mal formado."}, 400)
    if not isinstance(datos, dict):
        return _json({"ok": False, "error": "Se esperaba un formulario."}, 400)
    return _json(calcular(datos))


def descargar(peticion: Peticion) -> Respuesta:
    """El arrume como HTML autocontenido, para guardar o compartir."""
    try:
        contenido = exportar(peticion.parametros)
    except ArrumeError as error:
        return _texto(str(error), 400)
    return Respuesta(
        200,
        _TIPOS[".html"],
        contenido,
        {"Content-Disposition": 'attachment; filename="arrume.html"'},
    )


RUTAS: dict[tuple[str, str], Callable[[Peticion], Respuesta]] = {
    ("GET", "/"): pagina,
    ("GET", "/index.html"): pagina,
    ("GET", "/plotly.js"): plotlyjs,
    ("POST", "/api/arrume"): api_arrume,
    ("GET", "/descargar"): descargar,
}


def _estatico(ruta: str) -> Path | None:
    """Archivo de 'estaticos/' que corresponde a la ruta, si existe.

    Resuelve la ruta y comprueba que siga dentro de la carpeta, para que
    un '..' no saque el servidor de ahi.
    """
    destino = (ESTATICOS / ruta.lstrip("/")).resolve()
    if not destino.is_relative_to(ESTATICOS) or not destino.is_file():
        return None
    return destino


def atender(peticion: Peticion) -> Respuesta:
    """Resuelve una peticion. Funcion pura: ni sockets ni estado global."""
    manejador = RUTAS.get((peticion.metodo, peticion.ruta))
    if manejador is not None:
        return manejador(peticion)

    if peticion.metodo == "GET":
        archivo = _estatico(peticion.ruta)
        if archivo is not None:
            tipo = _TIPOS.get(archivo.suffix.lower(), "application/octet-stream")
            return Respuesta(200, tipo, archivo.read_bytes())

    return _texto(f"No encontrado: {peticion.ruta}", 404)


# =====================================================================
# Plomeria HTTP
# =====================================================================


class Manejador(BaseHTTPRequestHandler):
    """Traduce entre http.server y 'atender'. Aqui no hay ninguna decision."""

    server_version = "arrume"

    def do_GET(self) -> None:  # noqa: N802  (lo nombra http.server)
        self._responder("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._responder("POST")

    def _responder(self, metodo: str) -> None:
        partes = urlparse(self.path)
        largo = int(self.headers.get("Content-Length") or 0)
        peticion = Peticion(
            metodo=metodo,
            ruta=partes.path,
            parametros={
                clave: valores[0]
                for clave, valores in parse_qs(partes.query).items()
                if valores
            },
            cuerpo=self.rfile.read(largo) if largo else b"",
        )

        respuesta = atender(peticion)

        self.send_response(respuesta.estado)
        self.send_header("Content-Type", respuesta.tipo)
        self.send_header("Content-Length", str(len(respuesta.cuerpo)))
        for nombre, valor in respuesta.cabeceras.items():
            self.send_header(nombre, valor)
        self.end_headers()
        self.wfile.write(respuesta.cuerpo)

    def log_message(self, formato: str, *args: object) -> None:
        """Silencio: la consola es para el usuario, no para el trafico."""


def crear_servidor(puerto: int = 0) -> ThreadingHTTPServer:
    """Servidor escuchando solo en local. Puerto 0 = uno libre cualquiera."""
    return ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)


def main(argv: Sequence[str] | None = None) -> int:
    """Abre la interfaz y se queda sirviendo hasta que la cierres."""
    parser = argparse.ArgumentParser(
        prog="arrume-gui",
        description="Abre la interfaz grafica del generador de arrumes.",
    )
    parser.add_argument(
        "--puerto", type=int, default=0, metavar="N",
        help="puerto donde escuchar (0 = elige uno libre)",
    )
    parser.add_argument(
        "--no-abrir", dest="abrir", action="store_false", default=True,
        help="no abrir el navegador al arrancar",
    )
    args = parser.parse_args(argv)

    servidor = crear_servidor(args.puerto)
    direccion = f"http://127.0.0.1:{servidor.server_port}/"
    # flush: si la salida no va a una consola (un .bat redirigido, un log)
    # sin esto la direccion se queda en el buffer y no la ve nadie.
    print(f"Arrume abierto en {direccion}", flush=True)
    print("Deja esta ventana abierta mientras lo uses; Ctrl+C para cerrar.", flush=True)

    if args.abrir:
        threading.Timer(0.4, webbrowser.open, args=(direccion,)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado.", flush=True)
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

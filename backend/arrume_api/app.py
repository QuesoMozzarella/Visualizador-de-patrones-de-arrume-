"""Fabrica de la aplicacion Flask.

    create_app()                        configuracion por defecto
    create_app({"BASE_DE_DATOS": ...})  para los tests, u otra base

Configuracion (cada clave se puede dar tambien por variable de entorno):

  BASE_DE_DATOS        ARRUME_BD         archivo SQLite de los arrumes guardados
  FRONTEND             ARRUME_FRONTEND   carpeta con el build de React; si
                                         existe, Flask la sirve en '/'
  ORIGENES_PERMITIDOS  ARRUME_ORIGENES   origenes (separados por comas) que
                                         pueden llamar a la API desde otro
                                         dominio o puerto
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from .repositorio import RepositorioSqlite
from .rutas import api

# backend/arrume_api/app.py -> la raiz del repositorio
_RAIZ = Path(__file__).resolve().parents[2]


def _por_defecto(app: Flask) -> dict[str, Any]:
    origenes = os.environ.get("ARRUME_ORIGENES", "")
    return {
        "BASE_DE_DATOS": os.environ.get(
            "ARRUME_BD", str(Path(app.instance_path) / "arrume.sqlite3")
        ),
        "FRONTEND": os.environ.get(
            "ARRUME_FRONTEND", str(_RAIZ / "frontend" / "dist")
        ),
        "ORIGENES_PERMITIDOS": [o.strip() for o in origenes.split(",") if o.strip()],
    }


def create_app(configuracion: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.update(_por_defecto(app))
    if configuracion:
        app.config.update(configuracion)
    app.json.ensure_ascii = False  # type: ignore[attr-defined]

    Path(app.config["BASE_DE_DATOS"]).parent.mkdir(parents=True, exist_ok=True)
    app.extensions["repositorio"] = RepositorioSqlite(app.config["BASE_DE_DATOS"])
    app.register_blueprint(api)

    _cors(app)
    _errores_en_json(app)
    _servir_frontend(app)
    return app


def _cors(app: Flask) -> None:
    """Deja llamar a la API desde los origenes configurados, y solo esos."""

    @app.after_request
    def permitir(respuesta: Response) -> Response:
        origen = request.headers.get("Origin")
        if origen and origen in app.config["ORIGENES_PERMITIDOS"]:
            respuesta.headers["Access-Control-Allow-Origin"] = origen
            respuesta.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            respuesta.headers["Access-Control-Allow-Headers"] = "Content-Type"
            respuesta.headers["Vary"] = "Origin"
        return respuesta


def _errores_en_json(app: Flask) -> None:
    """En /api hasta los 404 y 405 responden JSON, como el resto."""

    @app.errorhandler(HTTPException)
    def en_json(error: HTTPException) -> Any:
        if not request.path.startswith("/api/"):
            return error
        return jsonify({"error": error.description}), error.code


def _servir_frontend(app: Flask) -> None:
    """Si hay un build de React, Flask lo sirve: un solo programa que abrir.

    Toda ruta que no sea de la API ni un archivo del build devuelve
    index.html, para que React maneje sus propias rutas.
    """
    carpeta = Path(app.config["FRONTEND"])
    if not (carpeta / "index.html").is_file():
        return

    @app.get("/", defaults={"ruta": ""})
    @app.get("/<path:ruta>")
    def frontend(ruta: str) -> Any:
        if ruta.startswith("api/"):
            return jsonify({"error": "No existe esa ruta de la API."}), 404
        if ruta and (carpeta / ruta).is_file():
            return send_from_directory(carpeta, ruta)
        return send_from_directory(carpeta, "index.html")

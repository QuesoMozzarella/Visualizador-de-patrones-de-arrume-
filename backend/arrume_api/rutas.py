"""Rutas de la API. Adaptador HTTP y nada mas.

Cada ruta lee el JSON, llama al servicio o al repositorio y responde JSON.
Las decisiones viven en arrume_api.servicio y en el paquete arrume.

  POST   /api/calcular              arma el arrume y devuelve cifras y geometria
  GET    /api/valores-iniciales     lo que muestra el formulario al abrir
  GET    /api/arrumes               los arrumes guardados, sin sus datos
  POST   /api/arrumes               guarda uno nuevo          {nombre, datos}
  GET    /api/arrumes/<id>          uno guardado, con sus datos
  PUT    /api/arrumes/<id>          lo reemplaza              {nombre, datos}
  DELETE /api/arrumes/<id>          lo borra
  POST   /api/informe               el informe en PDF   {datos, nombre?, imagen_*?}
"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request

from arrume.domain.errors import ArrumeError

from .repositorio import RepositorioArrumes
from .servicio import VALORES_INICIALES, calcular, informe, para_guardar

api = Blueprint("api", __name__, url_prefix="/api")


def _repositorio() -> RepositorioArrumes:
    repositorio: RepositorioArrumes = current_app.extensions["repositorio"]
    return repositorio


def _error(mensaje: str, estado: int) -> tuple[Response, int]:
    return jsonify({"error": mensaje}), estado


def _cuerpo() -> dict[str, Any] | None:
    """El JSON de la peticion si es un objeto; None si no lo es."""
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else None


@api.post("/calcular")
def ruta_calcular() -> Any:
    """Un dato invalido no es un error de HTTP: responde 200 con ok=false."""
    datos = _cuerpo()
    if datos is None:
        return _error("Se esperaba un objeto JSON con el formulario.", 400)
    return jsonify(calcular(datos))


@api.get("/valores-iniciales")
def ruta_valores_iniciales() -> Any:
    return jsonify(VALORES_INICIALES)


@api.get("/arrumes")
def ruta_listar() -> Any:
    return jsonify([guardado.resumen() for guardado in _repositorio().listar()])


@api.post("/arrumes")
def ruta_crear() -> Any:
    cuerpo = _cuerpo()
    if cuerpo is None:
        return _error("Se esperaba un objeto JSON con nombre y datos.", 400)
    try:
        nombre, datos = para_guardar(cuerpo)
    except ArrumeError as error:
        return _error(str(error), 422)
    return jsonify(_repositorio().crear(nombre, datos).completo()), 201


@api.get("/arrumes/<int:id>")
def ruta_obtener(id: int) -> Any:
    guardado = _repositorio().obtener(id)
    if guardado is None:
        return _error(f"No existe el arrume {id}.", 404)
    return jsonify(guardado.completo())


@api.put("/arrumes/<int:id>")
def ruta_actualizar(id: int) -> Any:
    cuerpo = _cuerpo()
    if cuerpo is None:
        return _error("Se esperaba un objeto JSON con nombre y datos.", 400)
    try:
        nombre, datos = para_guardar(cuerpo)
    except ArrumeError as error:
        return _error(str(error), 422)
    guardado = _repositorio().actualizar(id, nombre, datos)
    if guardado is None:
        return _error(f"No existe el arrume {id}.", 404)
    return jsonify(guardado.completo())


@api.delete("/arrumes/<int:id>")
def ruta_borrar(id: int) -> Any:
    if not _repositorio().borrar(id):
        return _error(f"No existe el arrume {id}.", 404)
    return "", 204


@api.post("/informe")
def ruta_informe() -> Any:
    cuerpo = _cuerpo()
    if cuerpo is None:
        return _error("Se esperaba un objeto JSON con los datos del arrume.", 400)
    try:
        pdf, archivo = informe(cuerpo)
    except ArrumeError as error:
        return _error(str(error), 422)
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{archivo}"'},
    )

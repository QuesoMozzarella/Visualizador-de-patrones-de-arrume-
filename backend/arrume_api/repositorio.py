"""Arrumes guardados: el puerto y su adaptador SQLite.

Las rutas hablan con RepositorioArrumes, no con sqlite3: cambiar de base
de datos es escribir otra clase que cumpla el protocolo.

Se guarda lo que el usuario escribio (medidas, pisos, acomodo), no el
resultado: el arrume se vuelve a calcular al abrirlo, asi que una mejora
del calculo le llega tambien a lo guardado.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ArrumeGuardado:
    id: int
    nombre: str
    datos: dict[str, Any]
    creado: str
    actualizado: str

    def resumen(self) -> dict[str, Any]:
        """Lo que hace falta para listarlo, sin los datos."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "creado": self.creado,
            "actualizado": self.actualizado,
        }

    def completo(self) -> dict[str, Any]:
        return {**self.resumen(), "datos": self.datos}


@runtime_checkable
class RepositorioArrumes(Protocol):
    def listar(self) -> list[ArrumeGuardado]: ...

    def obtener(self, id: int) -> ArrumeGuardado | None: ...

    def crear(self, nombre: str, datos: dict[str, Any]) -> ArrumeGuardado: ...

    def actualizar(
        self, id: int, nombre: str, datos: dict[str, Any]
    ) -> ArrumeGuardado | None: ...

    def borrar(self, id: int) -> bool: ...


_ESQUEMA = """
CREATE TABLE IF NOT EXISTS arrumes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT    NOT NULL,
    datos       TEXT    NOT NULL,
    creado      TEXT    NOT NULL,
    actualizado TEXT    NOT NULL
)
"""


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RepositorioSqlite:
    """Arrumes guardados en un archivo SQLite.

    Abre una conexion por operacion: Flask atiende en varios hilos y una
    conexion de sqlite3 no se comparte entre ellos.
    """

    def __init__(self, ruta: str | Path) -> None:
        self.ruta = str(ruta)
        with self._conexion() as conexion:
            conexion.execute(_ESQUEMA)

    @contextmanager
    def _conexion(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.row_factory = sqlite3.Row
            with conexion:  # commit al salir bien, rollback si algo falla
                yield conexion

    @staticmethod
    def _fila(fila: sqlite3.Row) -> ArrumeGuardado:
        return ArrumeGuardado(
            id=fila["id"],
            nombre=fila["nombre"],
            datos=json.loads(fila["datos"]),
            creado=fila["creado"],
            actualizado=fila["actualizado"],
        )

    def listar(self) -> list[ArrumeGuardado]:
        with self._conexion() as conexion:
            filas = conexion.execute(
                "SELECT * FROM arrumes ORDER BY actualizado DESC, id DESC"
            ).fetchall()
        return [self._fila(fila) for fila in filas]

    def obtener(self, id: int) -> ArrumeGuardado | None:
        with self._conexion() as conexion:
            fila = conexion.execute(
                "SELECT * FROM arrumes WHERE id = ?", (id,)
            ).fetchone()
        return self._fila(fila) if fila else None

    def crear(self, nombre: str, datos: dict[str, Any]) -> ArrumeGuardado:
        ahora = _ahora()
        with self._conexion() as conexion:
            cursor = conexion.execute(
                "INSERT INTO arrumes (nombre, datos, creado, actualizado) "
                "VALUES (?, ?, ?, ?)",
                (nombre, json.dumps(datos), ahora, ahora),
            )
            nuevo = cursor.lastrowid
        guardado = self.obtener(int(nuevo or 0))
        assert guardado is not None
        return guardado

    def actualizar(
        self, id: int, nombre: str, datos: dict[str, Any]
    ) -> ArrumeGuardado | None:
        with self._conexion() as conexion:
            cursor = conexion.execute(
                "UPDATE arrumes SET nombre = ?, datos = ?, actualizado = ? "
                "WHERE id = ?",
                (nombre, json.dumps(datos), _ahora(), id),
            )
            if cursor.rowcount == 0:
                return None
        return self.obtener(id)

    def borrar(self, id: int) -> bool:
        with self._conexion() as conexion:
            cursor = conexion.execute("DELETE FROM arrumes WHERE id = ?", (id,))
        return cursor.rowcount > 0

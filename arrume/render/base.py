"""Contratos de la capa de dibujo.

Son dos cosas distintas, y por eso son dos protocolos: armar la figura
(Renderer) y guardarla en un archivo (Exportador). Quien solo quiere la
figura -- un notebook, un test -- no tiene por que escribir en disco.

El dominio no conoce ninguno de los dos: es la CLI la que los elige.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..domain.models import Arrume


@runtime_checkable
class Renderer(Protocol):
    """Convierte un arrume en una figura dibujable."""

    nombre: str

    def render(self, arrume: Arrume) -> Any:
        ...


@runtime_checkable
class Exportador(Protocol):
    """Guarda una figura ya armada en un archivo."""

    extension: str

    def exportar(self, figura: Any, ruta: str, abrir: bool = False) -> str:
        """Escribe la figura y devuelve la ruta del archivo."""
        ...

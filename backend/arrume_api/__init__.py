"""API web de Arrume: Flask sobre el paquete arrume, con SQLite para guardar."""

from .app import create_app

__all__ = ["create_app"]

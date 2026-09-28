"""Errores del dominio.

Todos heredan de ArrumeError para que la capa de entrada (la API) pueda
capturarlos en un solo except y traducirlos a un mensaje para el usuario.
El dominio nunca imprime ni sabe de HTTP.
"""


class ArrumeError(Exception):
    """Error de negocio del generador de arrumes."""


class ConfiguracionInvalida(ArrumeError):
    """Los datos de entrada no describen un pallet, caja o arrume posible."""


class CajaNoCabe(ArrumeError):
    """Ninguna caja cabe sobre la superficie disponible."""


class AcomodoInvalido(ArrumeError):
    """El acomodo de un nivel se sale del pallet, se pisa o no es esa caja."""

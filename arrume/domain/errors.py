"""Errores del dominio.

Todos heredan de ArrumeError para que la capa de entrada (la CLI) pueda
capturarlos en un solo except y traducirlos a un mensaje y un codigo de
salida. El dominio nunca llama a sys.exit ni imprime nada.
"""


class ArrumeError(Exception):
    """Error de negocio del generador de arrumes."""


class ConfiguracionInvalida(ArrumeError):
    """Los datos de entrada no describen un pallet, caja o arrume posible."""


class CajaNoCabe(ArrumeError):
    """Ninguna caja cabe sobre la superficie disponible."""

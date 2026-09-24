"""Interfaz grafica: sirve una pagina local con el formulario y el arrume 3D.

Solo traduce entre el formulario y el nucleo; el calculo sigue viviendo en
arrume.stacking, el informe en arrume.reporting y el dibujo en arrume.render.
"""

from .servicio import VALORES_INICIALES, calcular, construir, exportar

__all__ = ["VALORES_INICIALES", "calcular", "construir", "exportar"]

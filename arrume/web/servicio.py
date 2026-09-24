"""Capa de servicio de la interfaz grafica.

Traduce entre lo que manda el formulario (texto, campos vacios) y el
dominio, y devuelve datos listos para pintar. No sabe nada de HTTP: recibe
un diccionario y devuelve un diccionario, y por eso se puede probar sin
levantar ningun servidor.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..domain.errors import ArrumeError, ConfiguracionInvalida
from ..domain.models import Arrume, Caja, Numero, Pallet, Restricciones
from ..render.plotly3d import ExportadorHTML, Plotly3D
from ..reporting import formatear, generar_informe
from ..stacking import construir_arrume
from ..trabazon import TRABAZONES

# Lo que ve el usuario al abrir la interfaz
VALORES_INICIALES: dict[str, Any] = {
    "pallet_ancho": 120,
    "pallet_profundidad": 100,
    "pallet_alto": 15,
    "caja_ancho": 40,
    "caja_profundidad": 30,
    "caja_alto": 25,
    "niveles": 5,
    "vuelo": 0,
    "trabado": True,
    "trabazon": "mejor",
    "altura_max": None,
    "peso_caja": None,
    "peso_max": None,
}

# Para que los mensajes de error hablen como el formulario, no como el codigo
_ETIQUETAS = {
    "pallet_ancho": "ancho del pallet",
    "pallet_profundidad": "profundidad del pallet",
    "pallet_alto": "alto del pallet",
    "caja_ancho": "ancho de la caja",
    "caja_profundidad": "profundidad de la caja",
    "caja_alto": "alto de la caja",
    "niveles": "numero de niveles",
    "vuelo": "vuelo",
    "altura_max": "altura maxima",
    "peso_caja": "peso de la caja",
    "peso_max": "peso maximo",
}


def _opcional(datos: Mapping[str, Any], clave: str) -> Numero | None:
    """Lee un campo numerico; vacio o ausente devuelve None."""
    bruto = datos.get(clave)
    if bruto is None or (isinstance(bruto, str) and not bruto.strip()):
        return None
    if isinstance(bruto, bool):
        raise ConfiguracionInvalida(f"El {_ETIQUETAS[clave]} debe ser un numero.")
    try:
        valor = float(bruto)
    except (TypeError, ValueError):
        raise ConfiguracionInvalida(
            f"El {_ETIQUETAS[clave]} debe ser un numero (recibido '{bruto}')."
        ) from None
    return int(valor) if valor.is_integer() else valor


def _obligatorio(datos: Mapping[str, Any], clave: str) -> Numero:
    """Lee un campo numerico que no puede quedar vacio."""
    valor = _opcional(datos, clave)
    if valor is None:
        raise ConfiguracionInvalida(f"Falta el {_ETIQUETAS[clave]}.")
    return valor


def _booleano(datos: Mapping[str, Any], clave: str, por_defecto: bool) -> bool:
    bruto = datos.get(clave, por_defecto)
    if isinstance(bruto, bool):
        return bruto
    return str(bruto).strip().lower() in {"1", "true", "si", "on"}


def construir(datos: Mapping[str, Any]) -> Arrume:
    """Arma el arrume a partir de los campos del formulario.

    Lanza ConfiguracionInvalida o CajaNoCabe, como el resto del dominio.
    """
    pallet = Pallet(
        _obligatorio(datos, "pallet_ancho"),
        _obligatorio(datos, "pallet_profundidad"),
        _obligatorio(datos, "pallet_alto"),
    )
    caja = Caja(
        _obligatorio(datos, "caja_ancho"),
        _obligatorio(datos, "caja_profundidad"),
        _obligatorio(datos, "caja_alto"),
    )
    niveles = _obligatorio(datos, "niveles")
    if isinstance(niveles, float):
        raise ConfiguracionInvalida("El numero de niveles debe ser entero.")

    restricciones = Restricciones(
        niveles=niveles,
        trabado=_booleano(datos, "trabado", True),
        vuelo=_opcional(datos, "vuelo") or 0,
        altura_max=_opcional(datos, "altura_max"),
        peso_caja=_opcional(datos, "peso_caja"),
        peso_max=_opcional(datos, "peso_max"),
    )

    nombre = str(datos.get("trabazon", "mejor"))
    if nombre not in TRABAZONES:
        raise ConfiguracionInvalida(f"Trabazon desconocida: '{nombre}'.")

    return construir_arrume(pallet, caja, restricciones, trabazon=TRABAZONES[nombre]())


def calcular(datos: Mapping[str, Any]) -> dict[str, Any]:
    """Respuesta completa para la interfaz: figura, cifras y avisos.

    Nunca lanza por datos malos: los errores viajan dentro del resultado
    para que la pagina los muestre donde toca.
    """
    try:
        arrume = construir(datos)
    except ArrumeError as error:
        return {"ok": False, "error": str(error)}

    informe = generar_informe(arrume)
    figura = Plotly3D().render(arrume)

    return {
        "ok": True,
        "figura": json.loads(figura.to_json()),
        "resumen": {
            "cajas_por_nivel": informe.cajas_por_nivel,
            "cajas_normales": informe.cajas_normales,
            "cajas_giradas": informe.cajas_giradas,
            "niveles": informe.niveles,
            "total_cajas": informe.total_cajas,
            "altura_total": informe.altura_total,
            "aprovechamiento": round(informe.aprovechamiento, 1),
            "peso_total": informe.peso_total,
            "trabado": informe.trabado,
            "traba": informe.traba,
            "trabazon": informe.trabazon,
            "trabazon_calidad": round(100 * informe.trabazon_calidad),
            "cajas_calcadas": informe.cajas_calcadas,
        },
        "avisos": list(informe.avisos),
        "texto": formatear(arrume, informe),
    }


def exportar(datos: Mapping[str, Any]) -> bytes:
    """HTML autocontenido del arrume, para descargar o compartir."""
    figura = Plotly3D().render(construir(datos))
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = str(Path(carpeta) / "arrume.html")
        ExportadorHTML("completo").exportar(figura, ruta)
        return Path(ruta).read_bytes()

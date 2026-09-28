"""Servicio de la API: del formulario al dominio y del dominio a JSON.

Traduce entre lo que manda el frontend (numeros o texto, campos vacios) y
el dominio, y devuelve datos listos para dibujar. No sabe nada de HTTP ni
de Flask: recibe un diccionario y devuelve un diccionario, y por eso se
prueba sin levantar ningun servidor.
"""

from __future__ import annotations

import base64
import binascii
import json
import unicodedata
from collections.abc import Mapping
from typing import Any

from arrume.domain.errors import ArrumeError, ConfiguracionInvalida
from arrume.domain.models import Arrume, Caja, Numero, Pallet, Pieza, Restricciones
from arrume.pisos import reparto
from arrume.reporting import formatear, generar_informe
from arrume.stacking import acomodo_normal, area_disponible, construir_por_pisos

# Lo que ve el usuario al abrir la interfaz. Sin 'acomodo', el acomodo del
# nivel lo calcula el programa; el usuario lo cambia desde ahi.
VALORES_INICIALES: dict[str, Any] = {
    "pallet_ancho": 120,
    "pallet_profundidad": 100,
    "pallet_alto": 15,
    "caja_ancho": 40,
    "caja_profundidad": 30,
    "caja_alto": 25,
    "niveles": 5,
    "cruzar": True,
    "iguales": 1,
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
    "iguales": "numero de primeros niveles iguales",
    "vuelo": "vuelo",
}


def _opcional(datos: Mapping[str, Any], clave: str) -> Numero | None:
    """Lee un campo numerico; vacio o ausente devuelve None."""
    bruto = datos.get(clave)
    if bruto is None or (isinstance(bruto, str) and not bruto.strip()):
        return None
    if isinstance(bruto, bool):
        raise ConfiguracionInvalida(f"El {_ETIQUETAS[clave]} debe ser un numero.")
    if isinstance(bruto, str):
        bruto = bruto.strip().replace(",", ".")  # "37,5" tambien vale
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

    Lanza ConfiguracionInvalida, CajaNoCabe o AcomodoInvalido, como el
    resto del dominio.
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

    restricciones = Restricciones(niveles=niveles, vuelo=_opcional(datos, "vuelo") or 0)
    return construir_por_pisos(
        pallet,
        caja,
        restricciones,
        _pisos(datos, restricciones.niveles),
        _acomodo(datos),
    )


def _pisos(datos: Mapping[str, Any], niveles: int) -> list[str]:
    """Si cada piso va normal o cruzado, de abajo arriba.

    'pisos' manda si viene: una lista, o las formas separadas por comas
    (asi llega en la URL de descarga). Si no, sale de 'cruzar' e 'iguales'.
    """
    pisos = datos.get("pisos")
    if isinstance(pisos, str):
        pisos = [forma.strip() for forma in pisos.split(",") if forma.strip()]
    if pisos:
        if not isinstance(pisos, list):
            raise ConfiguracionInvalida("Los pisos llegaron mal formados.")
        return [str(forma) for forma in pisos]

    iguales = _opcional(datos, "iguales")
    if iguales is None:
        iguales = 1
    if isinstance(iguales, float):
        raise ConfiguracionInvalida(
            "El numero de primeros niveles iguales debe ser entero."
        )
    return reparto(niveles, _booleano(datos, "cruzar", True), iguales)


def _acomodo(datos: Mapping[str, Any]) -> list[Pieza] | None:
    """Las cajas de un nivel tal como las puso el usuario, si las puso.

    Llega como lista de cajas {x, y, ancho, profundidad}, o como esa misma
    lista en texto JSON (asi viaja en la URL de descarga). Las coordenadas
    son del area disponible, con el vuelo dentro.
    """
    crudo = datos.get("acomodo")
    if isinstance(crudo, str):
        if not crudo.strip():
            return None
        try:
            crudo = json.loads(crudo)
        except json.JSONDecodeError:
            raise ConfiguracionInvalida("El acomodo llego mal formado.") from None
    if crudo is None:
        return None
    if not isinstance(crudo, list):
        raise ConfiguracionInvalida("El acomodo llego mal formado.")
    if not crudo:
        raise ConfiguracionInvalida(
            "El acomodo no tiene ninguna caja: pon alguna, o vuelve al automatico."
        )
    return [_pieza(caja) for caja in crudo]


def _pieza(caja: Any) -> Pieza:
    if not isinstance(caja, Mapping):
        raise ConfiguracionInvalida("El acomodo trae una caja mal formada.")
    try:
        return Pieza(
            float(caja["x"]),
            float(caja["y"]),
            float(caja["ancho"]),
            float(caja["profundidad"]),
        )
    except (KeyError, TypeError, ValueError):
        raise ConfiguracionInvalida(
            "El acomodo trae una caja sin medidas validas."
        ) from None


def calcular(datos: Mapping[str, Any]) -> dict[str, Any]:
    """Respuesta completa para el frontend: cifras, avisos y geometria.

    Nunca lanza por datos malos: los errores viajan dentro del resultado
    para que la pagina los muestre donde toca.
    """
    try:
        arrume = construir(datos)
    except ArrumeError as error:
        return {"ok": False, "error": str(error)}

    informe = generar_informe(arrume)
    area = area_disponible(arrume.pallet, arrume.restricciones)
    pallet = arrume.pallet

    return {
        "ok": True,
        "pallet": {
            "ancho": pallet.ancho,
            "profundidad": pallet.profundidad,
            "alto": pallet.alto,
        },
        # Cada caja del arrume en el espacio, para el dibujo 3D
        "cajas": [
            {
                "x": c.x,
                "y": c.y,
                "z": c.z,
                "ancho": c.ancho,
                "profundidad": c.profundidad,
                "alto": c.alto,
                "nivel": c.nivel,
            }
            for c in arrume.cajas
        ],
        "resumen": {
            "cajas_por_nivel": informe.cajas_por_nivel,
            "cajas_normales": informe.cajas_normales,
            "cajas_giradas": informe.cajas_giradas,
            "niveles": informe.niveles,
            "total_cajas": informe.total_cajas,
            "altura_total": informe.altura_total,
            "aprovechamiento": round(informe.aprovechamiento, 1),
            "intercalado": informe.trabado,
            # La superficie donde se puede poner una caja, con el vuelo dentro
            "area_ancho": area.ancho,
            "area_profundidad": area.profundidad,
        },
        "avisos": list(informe.avisos),
        "texto": formatear(arrume, informe),
        # El acomodo normal que se uso, para que el editor parta de ahi
        "acomodo": _cajas(acomodo_normal(arrume)),
        "plantas": _plantas(arrume),
    }


def _cajas(piezas: tuple[Pieza, ...]) -> list[dict[str, Numero]]:
    return [
        {"x": p.x, "y": p.y, "ancho": p.ancho, "profundidad": p.profundidad}
        for p in piezas
    ]


def _plantas(arrume: Arrume) -> list[dict[str, Any]]:
    """Cada nivel visto desde arriba, de abajo arriba: su forma y sus cajas."""
    return [
        {
            "forma": arrume.acomodo_de(nivel).nombre,
            "cajas": _cajas(arrume.acomodo_de(nivel).piezas),
        }
        for nivel in range(1, arrume.niveles + 1)
    ]



# Lo que se guarda de un arrume: lo que escribio el usuario, nada mas
CAMPOS_GUARDADOS = (
    "pallet_ancho",
    "pallet_profundidad",
    "pallet_alto",
    "caja_ancho",
    "caja_profundidad",
    "caja_alto",
    "niveles",
    "cruzar",
    "iguales",
    "pisos",
    "acomodo",
    "vuelo",
)

LARGO_MAXIMO_NOMBRE = 100


def para_guardar(cuerpo: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    """Nombre y datos listos para guardar, o un error que dice por que no.

    Solo se guarda un arrume que se puede armar: asi lo guardado siempre
    se vuelve a abrir.
    """
    nombre = cuerpo.get("nombre")
    if not isinstance(nombre, str) or not nombre.strip():
        raise ConfiguracionInvalida("Ponle un nombre al arrume para guardarlo.")
    nombre = nombre.strip()
    if len(nombre) > LARGO_MAXIMO_NOMBRE:
        raise ConfiguracionInvalida(
            f"El nombre no puede pasar de {LARGO_MAXIMO_NOMBRE} letras."
        )

    crudos = cuerpo.get("datos")
    if not isinstance(crudos, Mapping):
        raise ConfiguracionInvalida("Faltan los datos del arrume.")
    datos = {
        clave: crudos[clave]
        for clave in CAMPOS_GUARDADOS
        if clave in crudos and crudos[clave] is not None
    }
    construir(datos)
    return nombre, datos


# La imagen del 3D llega del navegador; se acota para no aceptar cualquier cosa
TAMANO_MAXIMO_IMAGEN = 10 * 1024 * 1024
_PREFIJO_PNG = "data:image/png;base64,"
_FIRMA_PNG = b"\x89PNG\r\n\x1a\n"


def informe(cuerpo: Mapping[str, Any]) -> tuple[bytes, str]:
    """El informe en PDF y el nombre de archivo con que descargarlo.

    'cuerpo' trae los 'datos' del arrume (lo mismo que calcular), un
    'nombre' opcional para el titulo y, opcionales, las imagenes que genera
    el navegador como PNG en data URL: 'imagen_3d' (el arrume),
    'imagen_caja' e 'imagen_pallet'.
    """
    from .informe_pdf import informe_pdf

    datos = cuerpo.get("datos")
    if not isinstance(datos, Mapping):
        raise ConfiguracionInvalida("Faltan los datos del arrume.")
    arrume = construir(datos)

    nombre = cuerpo.get("nombre")
    nombre = nombre.strip()[:LARGO_MAXIMO_NOMBRE] if isinstance(nombre, str) else ""

    pdf = informe_pdf(
        arrume,
        nombre,
        imagen_3d=_imagen(cuerpo.get("imagen_3d"), "del 3D"),
        imagen_caja=_imagen(cuerpo.get("imagen_caja"), "de la caja"),
        imagen_pallet=_imagen(cuerpo.get("imagen_pallet"), "del pallet"),
    )
    return pdf, _archivo(nombre)


def _imagen(crudo: Any, cual: str) -> bytes | None:
    """Una imagen PNG en data URL, ya decodificada; None si no vino."""
    if crudo in (None, ""):
        return None
    if not isinstance(crudo, str) or not crudo.startswith(_PREFIJO_PNG):
        raise ConfiguracionInvalida(f"La imagen {cual} tiene que ser un PNG.")
    codificada = crudo[len(_PREFIJO_PNG):]
    if len(codificada) > TAMANO_MAXIMO_IMAGEN * 4 // 3 + 4:
        raise ConfiguracionInvalida(f"La imagen {cual} es demasiado grande.")
    try:
        imagen = base64.b64decode(codificada, validate=True)
    except (binascii.Error, ValueError):
        raise ConfiguracionInvalida(f"La imagen {cual} llego mal formada.") from None
    if not imagen.startswith(_FIRMA_PNG):
        raise ConfiguracionInvalida(f"La imagen {cual} tiene que ser un PNG.")
    return imagen


def _archivo(nombre: str) -> str:
    """'Galletas 40x30' -> 'arrume-galletas-40x30.pdf', sin tildes ni raros."""
    plano = nombre.replace("×", "x")
    plano = unicodedata.normalize("NFKD", plano).encode("ascii", "ignore").decode()
    trozos = "".join(c if c.isalnum() else "-" for c in plano.lower()).split("-")
    limpio = "-".join(t for t in trozos if t)[:60]
    return f"arrume-{limpio}.pdf" if limpio else "arrume.pdf"

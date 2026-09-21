"""Modelos del dominio.

Regla: un objeto construido es un objeto valido. La validacion vive en
__post_init__, asi el resto del codigo deja de comprobar dimensiones.
Los valores no se convierten a float: si entran enteros, la aritmetica del
motor de empaquetado se mantiene exacta.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Union

from .errors import ConfiguracionInvalida

Numero = Union[int, float]


def _validar_numero(valor: object, nombre: str) -> None:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ConfiguracionInvalida(
            "{} debe ser un numero, no {}.".format(nombre, type(valor).__name__)
        )
    if not math.isfinite(valor):
        raise ConfiguracionInvalida("{} debe ser un numero finito.".format(nombre))


def _validar_positivo(valor: object, nombre: str) -> None:
    _validar_numero(valor, nombre)
    if valor <= 0:  # type: ignore[operator]
        raise ConfiguracionInvalida(
            "{} debe ser mayor que cero (recibido {}).".format(nombre, valor)
        )


def _validar_no_negativo(valor: object, nombre: str) -> None:
    _validar_numero(valor, nombre)
    if valor < 0:  # type: ignore[operator]
        raise ConfiguracionInvalida(
            "{} no puede ser negativo (recibido {}).".format(nombre, valor)
        )


@dataclass(frozen=True)
class Area:
    """Superficie rectangular en el plano XY (cm)."""

    ancho: Numero
    profundidad: Numero

    def __post_init__(self) -> None:
        _validar_positivo(self.ancho, "El ancho del area")
        _validar_positivo(self.profundidad, "La profundidad del area")

    @property
    def superficie(self) -> Numero:
        return self.ancho * self.profundidad


@dataclass(frozen=True)
class Pallet:
    """Plataforma sobre la que se apila. 'alto' es el grueso de la plataforma."""

    ancho: Numero
    profundidad: Numero
    alto: Numero

    def __post_init__(self) -> None:
        _validar_positivo(self.ancho, "El ancho del pallet")
        _validar_positivo(self.profundidad, "La profundidad del pallet")
        _validar_positivo(self.alto, "El alto del pallet")

    @property
    def superficie(self) -> Area:
        return Area(self.ancho, self.profundidad)


@dataclass(frozen=True)
class Caja:
    """Caja a acomodar. Solo se permite girarla sobre el eje Z."""

    ancho: Numero
    profundidad: Numero
    alto: Numero

    def __post_init__(self) -> None:
        _validar_positivo(self.ancho, "El ancho de la caja")
        _validar_positivo(self.profundidad, "La profundidad de la caja")
        _validar_positivo(self.alto, "El alto de la caja")

    @property
    def base(self) -> Area:
        return Area(self.ancho, self.profundidad)

    @property
    def volumen(self) -> Numero:
        return self.ancho * self.profundidad * self.alto


@dataclass(frozen=True)
class Restricciones:
    """Como se apila y que limites tiene el arrume."""

    niveles: int
    trabado: bool = True
    vuelo: Numero = 0
    altura_max: Optional[Numero] = None
    peso_caja: Optional[Numero] = None
    peso_max: Optional[Numero] = None

    def __post_init__(self) -> None:
        if isinstance(self.niveles, bool) or not isinstance(self.niveles, int):
            raise ConfiguracionInvalida(
                "Los niveles deben ser un entero, no {}.".format(
                    type(self.niveles).__name__
                )
            )
        if self.niveles < 1:
            raise ConfiguracionInvalida(
                "Debe haber al menos 1 nivel (recibido {}).".format(self.niveles)
            )
        if not isinstance(self.trabado, bool):
            raise ConfiguracionInvalida("El trabado debe ser True o False.")
        _validar_no_negativo(self.vuelo, "El vuelo")
        if self.altura_max is not None:
            _validar_positivo(self.altura_max, "La altura maxima")
        if self.peso_caja is not None:
            _validar_positivo(self.peso_caja, "El peso de la caja")
        if self.peso_max is not None:
            _validar_positivo(self.peso_max, "El peso maximo")
        if self.peso_max is not None and self.peso_caja is None:
            raise ConfiguracionInvalida(
                "Para controlar el peso maximo hace falta el peso de la caja."
            )


@dataclass(frozen=True)
class Pieza:
    """Una caja ubicada dentro del patron de un nivel (coordenadas del area)."""

    x: Numero
    y: Numero
    ancho: Numero
    profundidad: Numero

    def __post_init__(self) -> None:
        _validar_numero(self.x, "La coordenada x de la pieza")
        _validar_numero(self.y, "La coordenada y de la pieza")
        _validar_positivo(self.ancho, "El ancho de la pieza")
        _validar_positivo(self.profundidad, "La profundidad de la pieza")

    @property
    def x2(self) -> Numero:
        return self.x + self.ancho

    @property
    def y2(self) -> Numero:
        return self.y + self.profundidad

    @property
    def superficie(self) -> Numero:
        return self.ancho * self.profundidad


@dataclass(frozen=True)
class Colocacion:
    """Una caja ubicada en el arrume (coordenadas del pallet, en XYZ)."""

    x: Numero
    y: Numero
    z: Numero
    ancho: Numero
    profundidad: Numero
    alto: Numero
    nivel: int

    def __post_init__(self) -> None:
        _validar_numero(self.x, "La coordenada x de la colocacion")
        _validar_numero(self.y, "La coordenada y de la colocacion")
        _validar_numero(self.z, "La coordenada z de la colocacion")
        _validar_positivo(self.ancho, "El ancho de la colocacion")
        _validar_positivo(self.profundidad, "La profundidad de la colocacion")
        _validar_positivo(self.alto, "El alto de la colocacion")
        if isinstance(self.nivel, bool) or not isinstance(self.nivel, int):
            raise ConfiguracionInvalida("El nivel debe ser un entero.")
        if self.nivel < 0:
            raise ConfiguracionInvalida("El nivel no puede ser negativo.")

    @property
    def x2(self) -> Numero:
        return self.x + self.ancho

    @property
    def y2(self) -> Numero:
        return self.y + self.profundidad

    @property
    def z2(self) -> Numero:
        return self.z + self.alto

    @property
    def cuerpo(self) -> tuple:
        """Origen y dimensiones, como los espera la capa de dibujo."""
        return (self.x, self.y, self.z, self.ancho, self.profundidad, self.alto)


@dataclass(frozen=True)
class Arrume:
    """Resultado completo: el patron de un nivel y todas las cajas apiladas."""

    pallet: Pallet
    caja: Caja
    restricciones: Restricciones
    patron_base: tuple
    cajas: tuple
    estrategia: str

    def __post_init__(self) -> None:
        if not self.patron_base:
            raise ConfiguracionInvalida("Un arrume no puede tener un patron vacio.")

    @property
    def cajas_por_nivel(self) -> int:
        return len(self.patron_base)

    @property
    def total_cajas(self) -> int:
        return len(self.cajas)

    @property
    def niveles(self) -> int:
        return self.restricciones.niveles

    @property
    def altura_total(self) -> Numero:
        return self.pallet.alto + self.niveles * self.caja.alto

    @property
    def peso_total(self) -> Optional[Numero]:
        if self.restricciones.peso_caja is None:
            return None
        return self.total_cajas * self.restricciones.peso_caja

    @property
    def aprovechamiento(self) -> float:
        """Porcentaje de la superficie del pallet que cubre un nivel.

        Se mide contra el pallet, no contra el area disponible: si hay vuelo,
        las cajas cubren mas que la plataforma y el valor pasa del 100 %.
        """
        cubierto = sum(pieza.superficie for pieza in self.patron_base)
        return 100.0 * cubierto / self.pallet.superficie.superficie

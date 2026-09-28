"""Modelos del dominio.

Regla: un objeto construido es un objeto valido. La validacion vive en
__post_init__, asi el resto del codigo deja de comprobar dimensiones.
Los valores no se convierten a float: si entran enteros, la aritmetica del
motor de empaquetado se mantiene exacta.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import ConfiguracionInvalida

Numero = int | float

# Topes de tamano: por encima el calculo y el dibujo se vuelven lentos, y
# ningun arrume real se acerca (una caja de 7 x 6 cm en un pallet de
# 120 x 100 ya son unas 280 por piso)
MAXIMO_NIVELES = 100
MAXIMO_CAJAS_POR_NIVEL = 300


def _validar_numero(valor: object, nombre: str) -> None:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ConfiguracionInvalida(
            f"{nombre} debe ser un numero, no {type(valor).__name__}."
        )
    if not math.isfinite(valor):
        raise ConfiguracionInvalida(f"{nombre} debe ser un numero finito.")


def _validar_positivo(valor: object, nombre: str) -> None:
    _validar_numero(valor, nombre)
    if valor <= 0:  # type: ignore[operator]
        raise ConfiguracionInvalida(
            f"{nombre} debe ser mayor que cero (recibido {valor})."
        )


def _validar_no_negativo(valor: object, nombre: str) -> None:
    _validar_numero(valor, nombre)
    if valor < 0:  # type: ignore[operator]
        raise ConfiguracionInvalida(
            f"{nombre} no puede ser negativo (recibido {valor})."
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
    """Como se apila: cuantos niveles, si hay pisos cruzados y el vuelo.

    'trabado' es True cuando no todos los pisos llevan el mismo acomodo.
    """

    niveles: int
    trabado: bool = True
    vuelo: Numero = 0

    def __post_init__(self) -> None:
        if isinstance(self.niveles, bool) or not isinstance(self.niveles, int):
            raise ConfiguracionInvalida(
                f"Los niveles deben ser un entero, no {type(self.niveles).__name__}."
            )
        if self.niveles < 1:
            raise ConfiguracionInvalida(
                f"Debe haber al menos 1 nivel (recibido {self.niveles})."
            )
        if self.niveles > MAXIMO_NIVELES:
            raise ConfiguracionInvalida(
                f"El arrume puede tener hasta {MAXIMO_NIVELES} niveles "
                f"(recibido {self.niveles})."
            )
        if not isinstance(self.trabado, bool):
            raise ConfiguracionInvalida("El trabado debe ser True o False.")
        _validar_no_negativo(self.vuelo, "El vuelo")


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
    def cuerpo(self) -> tuple[Numero, ...]:
        """Origen y dimensiones, como los espera la capa de dibujo."""
        return (self.x, self.y, self.z, self.ancho, self.profundidad, self.alto)


@dataclass(frozen=True)
class Acomodo:
    """Como van las cajas en un nivel, con un nombre para poder asignarlo.

    Un arrume guarda los acomodos que usa y, aparte, cual va en cada nivel.
    Asi dos niveles pueden repetir el mismo acomodo sin duplicarlo, y se
    puede intercalar como se quiera en vez de alternar por paridad.
    """

    nombre: str
    piezas: tuple[Pieza, ...]

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ConfiguracionInvalida("Un acomodo necesita un nombre.")
        if not self.piezas:
            raise ConfiguracionInvalida(
                f"El acomodo '{self.nombre}' no tiene ninguna caja."
            )

    @property
    def cajas(self) -> int:
        return len(self.piezas)

    @property
    def superficie(self) -> Numero:
        return sum(pieza.superficie for pieza in self.piezas)


@dataclass(frozen=True)
class Arrume:
    """Resultado completo: los acomodos, que nivel lleva cual, y las cajas."""

    pallet: Pallet
    caja: Caja
    restricciones: Restricciones
    acomodos: tuple[Acomodo, ...]
    por_nivel: tuple[int, ...]
    cajas: tuple[Colocacion, ...]
    estrategia: str = ""

    def __post_init__(self) -> None:
        if not self.acomodos:
            raise ConfiguracionInvalida("Un arrume necesita al menos un acomodo.")
        if len(self.por_nivel) != self.restricciones.niveles:
            raise ConfiguracionInvalida(
                f"Hay {len(self.por_nivel)} niveles asignados "
                f"y el arrume tiene {self.restricciones.niveles}."
            )
        for numero, indice in enumerate(self.por_nivel, start=1):
            if not 0 <= indice < len(self.acomodos):
                raise ConfiguracionInvalida(
                    f"El nivel {numero} apunta a un acomodo que no existe."
                )

    def acomodo_de(self, nivel: int) -> Acomodo:
        """El acomodo de un nivel. El nivel 1 es el que se apoya en el pallet."""
        if not 1 <= nivel <= self.niveles:
            raise ConfiguracionInvalida(
                f"El arrume tiene {self.niveles} niveles; no existe el {nivel}."
            )
        return self.acomodos[self.por_nivel[nivel - 1]]

    def cajas_de_nivel(self, nivel: int) -> int:
        """Cuantas cajas lleva ese nivel. No tienen por que ser todas iguales."""
        return self.acomodo_de(nivel).cajas

    @property
    def patron_base(self) -> tuple[Pieza, ...]:
        """El acomodo del primer nivel."""
        return self.acomodo_de(1).piezas

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
    def aprovechamiento(self) -> float:
        """Porcentaje de la superficie del pallet que cubre un nivel.

        Se mide contra el pallet, no contra el area disponible: si hay vuelo,
        las cajas cubren mas que la plataforma y el valor pasa del 100 %.
        """
        cubierto = sum(pieza.superficie for pieza in self.patron_base)
        return 100.0 * cubierto / self.pallet.superficie.superficie

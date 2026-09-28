// Como se pintan las cajas en el 3D del arrume.
//
// La paleta por piso esta validada (scripts/validate_palette.js de la guia
// de visualizacion): cada piso se distingue del de arriba y del de abajo,
// tambien con daltonismo, incluido el salto del ultimo color al primero
// cuando hay mas de 8 pisos. Las aristas negras y el "Piso N" al pasar el
// raton refuerzan la separacion, porque tres tonos quedan claros sobre blanco.

import type { Forma } from "../tipos";
import { CARTON } from "./modelos3d";

export const PALETA_PISOS = [
  "#2a78d6", // azul
  "#eb6834", // naranja
  "#1baf7a", // aguamarina
  "#eda100", // amarillo
  "#e87ba4", // rosa
  "#008300", // verde
  "#4a3aa7", // violeta
  "#e34948", // rojo
];

// Normal y cruzado: el par mas separado de la paleta
export const COLOR_FORMA: Record<Forma, string> = {
  normal: "#2a78d6",
  cruzado: "#eb6834",
};

export type ModoColor = "pisos" | "forma" | "carton" | "uno";

export interface Colores {
  modo: ModoColor;
  /** El color de 'uno'. */
  color: string;
}

export const MODOS: { modo: ModoColor; nombre: string }[] = [
  { modo: "pisos", nombre: "Un color por piso" },
  { modo: "forma", nombre: "Normal y cruzado" },
  { modo: "carton", nombre: "Carton" },
  { modo: "uno", nombre: "Un solo color" },
];

export const COLORES_INICIALES: Colores = { modo: "pisos", color: "#2a78d6" };

/** El color del piso 'nivel' (0 = el de abajo). */
export function colorDePiso(nivel: number, forma: Forma | string, colores: Colores): string {
  switch (colores.modo) {
    case "forma":
      return forma === "cruzado" ? COLOR_FORMA.cruzado : COLOR_FORMA.normal;
    case "carton":
      return CARTON;
    case "uno":
      return /^#[0-9a-f]{6}$/i.test(colores.color) ? colores.color : COLORES_INICIALES.color;
    default:
      return PALETA_PISOS[nivel % PALETA_PISOS.length];
  }
}

const CLAVE = "arrume.colores";

/** La eleccion de colores de este navegador; la inicial si no hay o falla. */
export function coloresGuardados(): Colores {
  try {
    const guardado = JSON.parse(localStorage.getItem(CLAVE) ?? "null");
    if (guardado && MODOS.some((m) => m.modo === guardado.modo) && typeof guardado.color === "string") {
      return guardado;
    }
  } catch {
    // sin almacenamiento (modo privado, bloqueado): se usa la inicial
  }
  return COLORES_INICIALES;
}

export function guardarColores(colores: Colores): void {
  try {
    localStorage.setItem(CLAVE, JSON.stringify(colores));
  } catch {
    // no pasa nada: solo se pierde la preferencia al recargar
  }
}

// Como va cada piso. Es la misma regla que arrume/pisos.py: la pagina la
// necesita para pintar la lista al instante, sin esperar al backend.

import type { Forma } from "../tipos";

export const MAXIMO_PISOS = 100;

/** Un entero de un input, dentro de [minimo, maximo]; null si no sirve. */
export function entero(texto: string, minimo: number, maximo: number): number | null {
  const n = Math.round(Number(texto));
  if (texto.trim() === "" || !Number.isFinite(n) || n < minimo) return null;
  return Math.min(n, maximo);
}

/**
 * La forma del piso i (0 = el de abajo): los primeros 'iguales' van
 * normales y del siguiente en adelante se turnan cruzado, normal...
 */
export function segunRegla(i: number, cruzar: boolean, iguales: number): Forma {
  if (!cruzar || i < iguales) return "normal";
  return (i - iguales) % 2 === 0 ? "cruzado" : "normal";
}

export function reparto(pisos: number, cruzar: boolean, iguales: number): Forma[] {
  return Array.from({ length: pisos }, (_, i) => segunRegla(i, cruzar, iguales));
}

/** Cambia cuantos pisos hay conservando lo que ya estaba elegido. */
export function ajustar(
  actuales: Forma[],
  pisos: number,
  cruzar: boolean,
  iguales: number,
): Forma[] {
  const nuevos = actuales.slice(0, pisos);
  for (let i = nuevos.length; i < pisos; i++) nuevos.push(segunRegla(i, cruzar, iguales));
  return nuevos;
}

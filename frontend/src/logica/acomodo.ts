// Geometria del editor de acomodo. Funciones puras: reciben cajas y
// devuelven cajas nuevas, sin tocar las que reciben, para que React vea
// cada cambio.
//
// La validacion definitiva la hace el backend; esta es para marcar en rojo
// al instante, mientras se arrastra.

import type { Area, Caja2D } from "../tipos";

export const TOL = 0.001;

export function seSale(c: Caja2D, area: Area): boolean {
  return (
    c.x < -TOL ||
    c.y < -TOL ||
    c.x + c.ancho > area.ancho + TOL ||
    c.y + c.profundidad > area.fondo + TOL
  );
}

export function sePisan(a: Caja2D, b: Caja2D): boolean {
  const dx = Math.min(a.x + a.ancho, b.x + b.ancho) - Math.max(a.x, b.x);
  const dy = Math.min(a.y + a.profundidad, b.y + b.profundidad) - Math.max(a.y, b.y);
  return dx > TOL && dy > TOL;
}

/** Indices de las cajas que se salen o se pisan con otra. */
export function malas(cajas: Caja2D[], area: Area): Set<number> {
  const fuera = new Set<number>();
  cajas.forEach((a, i) => {
    if (seSale(a, area)) fuera.add(i);
    for (let j = i + 1; j < cajas.length; j++) {
      if (sePisan(a, cajas[j])) {
        fuera.add(i);
        fuera.add(j);
      }
    }
  });
  return fuera;
}

/** Porcentaje del area que cubren las cajas. */
export function cubierto(cajas: Caja2D[], area: Area): number {
  const suma = cajas.reduce((s, c) => s + c.ancho * c.profundidad, 0);
  return (100 * suma) / (area.ancho * area.fondo);
}

/** El candidato mas cercano a 'valor' si esta a menos de 'radio'. */
export function imantar(valor: number, candidatos: number[], radio: number): number {
  let mejor = valor;
  let distancia = radio;
  for (const c of candidatos) {
    const d = Math.abs(valor - c);
    if (d < distancia) {
      distancia = d;
      mejor = c;
    }
  }
  return mejor;
}

/**
 * Pone la caja i en (x, y), pegandola a los bordes del pallet y de las
 * otras cajas si pasa cerca. Si no se pega a nada, redondea al cm.
 */
export function mover(cajas: Caja2D[], i: number, x: number, y: number, area: Area): Caja2D[] {
  const c = cajas[i];
  const radio = Math.max(1.5, Math.max(area.ancho, area.fondo) / 50);
  const xs = [0, area.ancho - c.ancho];
  const ys = [0, area.fondo - c.profundidad];
  cajas.forEach((o, j) => {
    if (j === i) return;
    xs.push(o.x, o.x + o.ancho, o.x - c.ancho, o.x + o.ancho - c.ancho);
    ys.push(o.y, o.y + o.profundidad, o.y - c.profundidad, o.y + o.profundidad - c.profundidad);
  });
  const nx = imantar(x, xs, radio);
  const ny = imantar(y, ys, radio);
  return reemplazar(cajas, i, {
    ...c,
    x: nx === x ? Math.round(x) : nx,
    y: ny === y ? Math.round(y) : ny,
  });
}

/** Mueve la caja i sin imanes, por ejemplo con las flechas. */
export function desplazar(cajas: Caja2D[], i: number, dx: number, dy: number): Caja2D[] {
  const c = cajas[i];
  return reemplazar(cajas, i, { ...c, x: c.x + dx, y: c.y + dy });
}

/** Gira la caja i un cuarto de vuelta; si al girar se sale, la mete. */
export function girar(cajas: Caja2D[], i: number, area: Area): Caja2D[] {
  const c = cajas[i];
  const ancho = c.profundidad;
  const profundidad = c.ancho;
  return reemplazar(cajas, i, {
    ancho,
    profundidad,
    x: Math.max(0, Math.min(c.x, area.ancho - ancho)),
    y: Math.max(0, Math.min(c.y, area.fondo - profundidad)),
  });
}

export function quitar(cajas: Caja2D[], i: number): Caja2D[] {
  return cajas.filter((_, j) => j !== i);
}

/**
 * El primer sitio libre para una caja ancho x fondo, de abajo arriba y de
 * izquierda a derecha, probando las esquinas que dejan las otras cajas.
 */
export function hueco(cajas: Caja2D[], ancho: number, fondo: number, area: Area): Caja2D | null {
  const xs = [0, ...cajas.map((c) => c.x + c.ancho)].sort((a, b) => a - b);
  const ys = [0, ...cajas.map((c) => c.y + c.profundidad)].sort((a, b) => a - b);
  for (const y of ys) {
    for (const x of xs) {
      const nueva = { x, y, ancho, profundidad: fondo };
      if (!seSale(nueva, area) && cajas.every((o) => !sePisan(nueva, o))) return nueva;
    }
  }
  return null;
}

/** Agrega una caja en el primer hueco, derecha o, si no cabe, girada. */
export function poner(cajas: Caja2D[], ancho: number, fondo: number, area: Area): Caja2D[] | null {
  const nueva = hueco(cajas, ancho, fondo, area) ?? hueco(cajas, fondo, ancho, area);
  return nueva ? [...cajas, nueva] : null;
}

function reemplazar(cajas: Caja2D[], i: number, caja: Caja2D): Caja2D[] {
  return cajas.map((c, j) => (j === i ? caja : c));
}

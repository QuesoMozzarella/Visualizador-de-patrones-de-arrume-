// Modelos 3D de la caja y del pallet, hechos con las medidas que se meten
// en el formulario, con sus cotas.

import { aristas, malla, type Cuerpo } from "./malla3d";

export const MADERA = "#b58b55";
export const MADERA_OSCURA = "#5b4128";
export const CARTON = "#c9a36a";
export const CINTA = "#8a6a3c";

const entre = (valor: number, minimo: number, maximo: number) =>
  Math.min(maximo, Math.max(minimo, valor));

/**
 * Un pallet de bloques, como el europallet, a la medida dada:
 *
 *   - tablas de arriba a lo largo del ancho (X), repartidas en el fondo,
 *   - tres travesanos a lo largo del fondo (Y) que las sostienen,
 *   - nueve tacos (3 x 3) debajo de los travesanos,
 *   - tres tablas de abajo a lo largo del ancho, bajo cada fila de tacos.
 *
 * La cara de arriba queda justo en z = alto. Si el pallet es tan delgado
 * que no caben tablas y tacos, se dibuja como una plancha.
 */
export function piezasPallet(ancho: number, fondo: number, alto: number): Cuerpo[] {
  const tabla = entre(alto * 0.15, 1.2, 2.5);
  const taco = alto - 3 * tabla;
  if (taco < 1) return [[0, 0, 0, ancho, fondo, alto]];

  const anchoTaco = entre(ancho * 0.12, 5, 16); // a lo largo de X
  const fondoTaco = entre(fondo * 0.12, 5, 16); // a lo largo de Y
  const xs = [0, (ancho - anchoTaco) / 2, ancho - anchoTaco];
  const ys = [0, (fondo - fondoTaco) / 2, fondo - fondoTaco];
  const piezas: Cuerpo[] = [];

  // Abajo: una tabla por fila de tacos
  for (const y of ys) piezas.push([0, y, 0, ancho, fondoTaco, tabla]);
  // Los nueve tacos
  for (const x of xs) for (const y of ys) piezas.push([x, y, tabla, anchoTaco, fondoTaco, taco]);
  // Travesanos, de lado a lado del fondo
  for (const x of xs) piezas.push([x, 0, tabla + taco, anchoTaco, fondo, tabla]);

  // Tablas de arriba: las dos de los bordes y el resto repartidas
  const cuantas = Math.max(3, Math.round(fondo / 20));
  const anchoTabla = entre(fondo / (cuantas * 1.6), 6, 15);
  const paso = (fondo - anchoTabla) / (cuantas - 1);
  for (let n = 0; n < cuantas; n++) {
    piezas.push([0, n * paso, alto - tabla, ancho, anchoTabla, tabla]);
  }
  return piezas;
}

/** La caja cerrada, con la cinta que la sella por arriba a lo largo. */
export function piezasCaja(ancho: number, fondo: number, alto: number): { caja: Cuerpo; cinta: Cuerpo } {
  const anchoCinta = Math.min(5, fondo * 0.15);
  const grueso = Math.max(0.15, alto * 0.006);
  return {
    caja: [0, 0, 0, ancho, fondo, alto],
    cinta: [0, (fondo - anchoCinta) / 2, alto, ancho, anchoCinta, grueso],
  };
}

const fmt = (valor: number) => `${Number(valor.toFixed(2))} cm`;

/**
 * Las tres cotas (ancho, fondo, alto) por fuera del objeto: lineas con sus
 * topes y el rotulo de la medida en el medio.
 */
export function cotas(ancho: number, fondo: number, alto: number, letra = 13) {
  const s = Math.max(ancho, fondo, alto) * 0.08; // separacion del objeto
  const t = s * 0.35; // largo de los topes
  const segmentos: [number, number, number][][] = [
    // Ancho, por delante y abajo
    [[0, -s, 0], [ancho, -s, 0]], [[0, -s - t, 0], [0, -s + t, 0]], [[ancho, -s - t, 0], [ancho, -s + t, 0]],
    // Fondo, por la derecha y abajo
    [[ancho + s, 0, 0], [ancho + s, fondo, 0]], [[ancho + s - t, 0, 0], [ancho + s + t, 0, 0]], [[ancho + s - t, fondo, 0], [ancho + s + t, fondo, 0]],
    // Alto, en la esquina delantera izquierda (lejos de la del fondo)
    [[-s, -s, 0], [-s, -s, alto]], [[-s - t, -s, 0], [-s + t, -s, 0]], [[-s - t, -s, alto], [-s + t, -s, alto]],
  ];
  const x: (number | null)[] = [], y: (number | null)[] = [], z: (number | null)[] = [];
  for (const [a, b] of segmentos) {
    x.push(a[0], b[0], null); y.push(a[1], b[1], null); z.push(a[2], b[2], null);
  }
  const rotulo = (px: number, py: number, pz: number, texto: string) => ({
    x: px, y: py, z: pz, text: texto, showarrow: false,
    font: { size: letra, color: "#000000", family: "Bahnschrift, Arial Narrow, sans-serif" },
    bgcolor: "rgba(255,255,255,0.85)",
  });
  return {
    linea: {
      type: "scatter3d" as const, mode: "lines" as const, x, y, z,
      line: { color: "#4a4e4b", width: 3 }, hoverinfo: "skip" as const, showlegend: false,
    },
    rotulos: [
      rotulo(ancho / 2, -s * 1.9, 0, `ancho ${fmt(ancho)}`),
      rotulo(ancho + s * 1.9, fondo / 2, 0, `fondo ${fmt(fondo)}`),
      rotulo(-s * 1.6, -s * 1.6, alto / 2, `alto ${fmt(alto)}`),
    ],
  };
}

function escena(rotulos: object[], ejes = false) {
  const eje = { visible: ejes, showbackground: false, title: { text: "" } };
  return {
    scene: {
      xaxis: eje, yaxis: eje, zaxis: eje,
      aspectmode: "data" as const,
      camera: { eye: { x: 1.8, y: -2.05, z: 1.35 } }, // lejos: deja sitio a las cotas
      annotations: rotulos,
    },
    showlegend: false,
    margin: { l: 0, r: 0, t: 0, b: 0 },
    paper_bgcolor: "#ffffff",
    uirevision: "modelo",
  };
}

/** 'letra' es el tamano de las cotas: mas grande para la imagen del informe. */
export function figuraCaja(ancho: number, fondo: number, alto: number, letra = 13) {
  const { caja, cinta } = piezasCaja(ancho, fondo, alto);
  const c = cotas(ancho, fondo, alto, letra);
  return {
    data: [
      malla([caja], CARTON, `Caja ${fmt(ancho)} x ${fmt(fondo)} x ${fmt(alto)}`),
      malla([cinta], CINTA, "Cinta"),
      aristas([caja], "#3b2a14", 3),
      c.linea,
    ],
    layout: escena(c.rotulos),
  };
}

export function figuraPallet(ancho: number, fondo: number, alto: number, letra = 13) {
  const piezas = piezasPallet(ancho, fondo, alto);
  const c = cotas(ancho, fondo, alto, letra);
  return {
    data: [
      malla(piezas, MADERA, `Pallet ${fmt(ancho)} x ${fmt(fondo)} x ${fmt(alto)}`),
      aristas(piezas, MADERA_OSCURA, 2),
      c.linea,
    ],
    layout: escena(c.rotulos),
  };
}

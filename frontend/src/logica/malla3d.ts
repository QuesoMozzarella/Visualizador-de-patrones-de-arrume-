// Piezas basicas para dibujar cajas en Plotly: volumenes y aristas.
// Todo lo 3D (el arrume, la caja suelta, el pallet) se arma con esto.

/** Un prisma recto: origen (x, y, z) y medidas (dx, dy, dz), en cm. */
export type Cuerpo = [number, number, number, number, number, number];

// Las 12 caras triangulares de una caja, con las normales hacia afuera
const CARAS: [number, number, number][] = [
  [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
  [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
  [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7],
];

const ARISTAS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 0],
  [4, 5], [5, 6], [6, 7], [7, 4],
  [0, 4], [1, 5], [2, 6], [3, 7],
];

export function vertices([x, y, z, dx, dy, dz]: Cuerpo): [number, number, number][] {
  return [
    [x, y, z], [x + dx, y, z], [x + dx, y + dy, z], [x, y + dy, z],
    [x, y, z + dz], [x + dx, y, z + dz], [x + dx, y + dy, z + dz], [x, y + dy, z + dz],
  ];
}

/** Varias cajas en un solo Mesh3d: mucho mas rapido que uno por caja. */
export function malla(cuerpos: Cuerpo[], color: string, nombre: string, etiquetas?: string[]) {
  const x: number[] = [], y: number[] = [], z: number[] = [];
  const i: number[] = [], j: number[] = [], k: number[] = [];
  const texto: string[] = [];
  cuerpos.forEach((cuerpo, n) => {
    for (const [px, py, pz] of vertices(cuerpo)) {
      x.push(px); y.push(py); z.push(pz);
      texto.push(etiquetas ? etiquetas[n] : nombre);
    }
    for (const [a, b, c] of CARAS) {
      i.push(8 * n + a); j.push(8 * n + b); k.push(8 * n + c);
    }
  });
  return {
    type: "mesh3d" as const,
    x, y, z, i, j, k,
    color, flatshading: true, name: nombre, text: texto, hoverinfo: "text" as const,
    // Luz algo mas marcada que la de fabrica, para que se lean las caras
    lighting: { ambient: 0.65, diffuse: 0.6, specular: 0.05, roughness: 0.9 },
  };
}

/** Todas las aristas en un solo trazo, cortado con null entre segmentos. */
export function aristas(cuerpos: Cuerpo[], color = "#1a1a1a", ancho = 2) {
  const x: (number | null)[] = [], y: (number | null)[] = [], z: (number | null)[] = [];
  for (const cuerpo of cuerpos) {
    const v = vertices(cuerpo);
    for (const [a, b] of ARISTAS) {
      x.push(v[a][0], v[b][0], null);
      y.push(v[a][1], v[b][1], null);
      z.push(v[a][2], v[b][2], null);
    }
  }
  return {
    type: "scatter3d" as const,
    mode: "lines" as const,
    x, y, z,
    line: { color, width: ancho },
    hoverinfo: "skip" as const,
    showlegend: false,
  };
}

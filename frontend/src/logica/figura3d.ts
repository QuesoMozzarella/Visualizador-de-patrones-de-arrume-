// Arma la figura 3D del arrume para Plotly: el pallet, un volumen por piso
// y las aristas de todas las cajas. El backend solo manda donde va cada
// caja; como se dibuja es cosa del frontend.

import type { Caja3D } from "../tipos";
import { COLORES_INICIALES, colorDePiso, type Colores } from "./colores";
import { aristas, malla, type Cuerpo } from "./malla3d";
import { MADERA, MADERA_OSCURA, piezasPallet } from "./modelos3d";

const cuerpo = (c: Caja3D): Cuerpo => [c.x, c.y, c.z, c.ancho, c.profundidad, c.alto];

export function figura(
  pallet: { ancho: number; profundidad: number; alto: number },
  cajas: Caja3D[],
  formas: string[],
  colores: Colores = COLORES_INICIALES,
) {
  const plataforma = piezasPallet(pallet.ancho, pallet.profundidad, pallet.alto);
  const pisos = Math.max(0, ...cajas.map((c) => c.nivel + 1));
  const data: object[] = [
    malla(plataforma, MADERA, "Pallet"),
    aristas(plataforma, MADERA_OSCURA, 1.5),
  ];

  for (let nivel = 0; nivel < pisos; nivel++) {
    const del = cajas.filter((c) => c.nivel === nivel);
    const forma = formas[nivel] ?? "";
    data.push(
      malla(
        del.map(cuerpo),
        colorDePiso(nivel, forma, colores),
        `Piso ${nivel + 1}`,
        del.map((_, n) => `Piso ${nivel + 1} (${forma}) - caja ${n + 1}`),
      ),
    );
  }
  data.push(aristas(cajas.map(cuerpo)));

  const layout = {
    scene: {
      xaxis: { title: { text: "Ancho (X) cm" } },
      yaxis: { title: { text: "Fondo (Y) cm" } },
      zaxis: { title: { text: "Alto (Z) cm" } },
      aspectmode: "data" as const,
      camera: { eye: { x: 1.6, y: -1.6, z: 1.1 } },
    },
    showlegend: false,
    margin: { l: 0, r: 0, t: 6, b: 0 },
    paper_bgcolor: "#ffffff",
    uirevision: "arrume", // conserva el giro de camara entre recalculos
  };
  return { data, layout };
}

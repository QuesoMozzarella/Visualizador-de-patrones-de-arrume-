// Los modelos 3D como imagenes PNG, para meterlos en el informe. Plotly se
// carga aqui dentro para no sumarlo a la primera carga de la pagina.

import type { Calculo } from "../tipos";
import type { Colores } from "./colores";
import { figura } from "./figura3d";
import { figuraCaja, figuraPallet } from "./modelos3d";

interface Figura {
  data: object[];
  layout: object;
}

async function png(f: Figura, ancho: number, alto: number, margen = 0): Promise<string> {
  const { default: Plotly } = await import("plotly.js-dist-min");
  const m = { l: margen, r: margen, t: margen / 3, b: margen / 3 };
  return Plotly.toImage(
    { data: f.data as Plotly.Data[], layout: { ...f.layout, margin: m } },
    { format: "png", width: ancho, height: alto },
  );
}

export interface Imagenes {
  imagen_3d?: string;
  imagen_caja?: string;
  imagen_pallet?: string;
}

/**
 * El arrume, la caja y el pallet como PNG. Si alguno no se puede dibujar
 * (sin WebGL, por ejemplo) se omite: el informe sale igual sin esa imagen.
 */
export async function imagenesInforme(
  calculo: Calculo,
  caja: [number, number, number],
  colores: Colores,
): Promise<Imagenes> {
  const { ancho, profundidad, alto } = calculo.pallet;
  const [arrume, deCaja, dePallet] = await Promise.allSettled([
    png(
      figura(calculo.pallet, calculo.cajas, calculo.plantas.map((p) => p.forma), colores),
      1200,
      800,
    ),
    // En el PDF la imagen va a media hoja: cotas con letra grande
    // (con margen, para que los rotulos de las cotas no se corten en el borde)
    png(figuraCaja(...caja, 30), 900, 750, 60),
    png(figuraPallet(ancho, profundidad, alto, 30), 900, 750, 60),
  ]);
  const valor = (r: PromiseSettledResult<string>) => (r.status === "fulfilled" ? r.value : undefined);
  return {
    imagen_3d: valor(arrume),
    imagen_caja: valor(deCaja),
    imagen_pallet: valor(dePallet),
  };
}

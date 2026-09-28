import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import type { Colores } from "../logica/colores";
import { figura } from "../logica/figura3d";
import type { Calculo } from "../tipos";

interface Props {
  calculo: Calculo;
  visible: boolean;
  colores: Colores;
}

export default function Vista3D({ calculo, visible, colores }: Props) {
  const lienzo = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!lienzo.current) return;
    const { data, layout } = figura(
      calculo.pallet,
      calculo.cajas,
      calculo.plantas.map((p) => p.forma),
      colores,
    );
    // react() reutiliza la escena: no parpadea y conserva el giro de camara
    void Plotly.react(lienzo.current, data as Plotly.Data[], layout, {
      responsive: true,
      displaylogo: false,
      toImageButtonOptions: { filename: "arrume", format: "png", scale: 2 },
    });
  }, [calculo, colores]);

  // Al volver a la pestana el lienzo pudo cambiar de tamano estando oculto
  useEffect(() => {
    if (visible && lienzo.current) Plotly.Plots.resize(lienzo.current);
  }, [visible]);

  useEffect(() => {
    const div = lienzo.current;
    return () => {
      if (div) Plotly.purge(div);
    };
  }, []);

  return <div id="arrume" ref={lienzo} hidden={!visible} />;
}

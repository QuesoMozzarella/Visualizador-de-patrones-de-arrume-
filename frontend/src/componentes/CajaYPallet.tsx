import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import { figuraCaja, figuraPallet } from "../logica/modelos3d";

type Medidas3 = [number, number, number];

interface Props {
  caja: Medidas3;
  pallet: Medidas3;
}

const valida = (m: Medidas3) => m.every((v) => Number.isFinite(v) && v > 0);

function Modelo({ figura }: { figura: { data: object[]; layout: object } }) {
  const lienzo = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!lienzo.current) return;
    void Plotly.react(lienzo.current, figura.data as Plotly.Data[], figura.layout, {
      responsive: true,
      displaylogo: false,
      toImageButtonOptions: { format: "png", scale: 2 },
    });
  }, [figura]);

  useEffect(() => {
    const div = lienzo.current;
    return () => {
      if (div) Plotly.purge(div);
    };
  }, []);

  return <div className="modelo-lienzo" ref={lienzo} />;
}

/** La caja y el pallet sueltos, en 3D y con sus medidas. */
export default function CajaYPallet({ caja, pallet }: Props) {
  const [ca, cf, ch] = caja;
  const [pa, pf, ph] = pallet;
  return (
    <div className="modelos">
      <figure className="modelo">
        <figcaption>
          <b>Caja</b> {ca} × {cf} × {ch} cm
        </figcaption>
        {valida(caja) ? (
          <Modelo figura={figuraCaja(ca, cf, ch)} />
        ) : (
          <p className="nota-campo">Faltan medidas de la caja.</p>
        )}
      </figure>
      <figure className="modelo">
        <figcaption>
          <b>Pallet</b> {pa} × {pf} × {ph} cm
        </figcaption>
        {valida(pallet) ? (
          <Modelo figura={figuraPallet(pa, pf, ph)} />
        ) : (
          <p className="nota-campo">Faltan medidas del pallet.</p>
        )}
      </figure>
    </div>
  );
}

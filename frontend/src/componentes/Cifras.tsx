import type { ReactNode } from "react";
import type { Resumen } from "../tipos";

function Celda({ cantidad, unidad, rotulo, detalle }: {
  cantidad: ReactNode;
  unidad?: string;
  rotulo: string;
  detalle?: string;
}) {
  return (
    <div className="celda">
      <div className="cantidad">
        {cantidad}
        {unidad && <u> {unidad}</u>}
      </div>
      <div className="rotulo">{rotulo}</div>
      {detalle && <div className="detalle">{detalle}</div>}
    </div>
  );
}

export function Cifras({ r }: { r: Resumen }) {
  return (
    <div className="cifras">
      <Celda cantidad={r.total_cajas} rotulo="cajas en el arrume" detalle={`${r.niveles} pisos`} />
      <Celda
        cantidad={r.cajas_por_nivel}
        rotulo="por piso"
        detalle={`${r.cajas_normales} derechas, ${r.cajas_giradas} giradas`}
      />
      <Celda cantidad={r.altura_total} unidad="cm" rotulo="de alto" />
      <Celda cantidad={r.aprovechamiento} unidad="%" rotulo="del pallet cubierto" />
    </div>
  );
}

export function Avisos({ avisos, error }: { avisos: string[]; error: string | null }) {
  return (
    <div aria-live="polite">
      {error && (
        <div className="banda parada">
          <div className="cinta" />
          <div className="dicho">
            <b>El arrume no se puede armar</b>
            {error}
          </div>
        </div>
      )}
      {avisos.map((aviso) => (
        <div className="banda precaucion" key={aviso}>
          <div className="cinta" />
          <div className="dicho">
            <b>Precaucion</b>
            {aviso}
          </div>
        </div>
      ))}
    </div>
  );
}

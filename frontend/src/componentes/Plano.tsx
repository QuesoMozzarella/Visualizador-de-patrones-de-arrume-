import { forwardRef, type ReactNode, type SVGProps } from "react";
import type { Area } from "../tipos";

interface Props extends Omit<SVGProps<SVGSVGElement>, "children"> {
  area: Area;
  margen?: number;
  children?: ReactNode;
}

/**
 * El pallet visto desde arriba, en cm, con la Y hacia arriba como en el
 * 3D. Lo que va dentro se dibuja en coordenadas del pallet.
 */
export const Plano = forwardRef<SVGGElement, Props>(function Plano(
  { area, margen = 3, children, ...resto },
  grupo,
) {
  const caja = `${-margen} ${-margen} ${area.ancho + 2 * margen} ${area.fondo + 2 * margen}`;
  return (
    <svg viewBox={caja} preserveAspectRatio="xMidYMid meet" {...resto}>
      <g ref={grupo} transform={`translate(0,${area.fondo}) scale(1,-1)`}>
        <rect className="suelo" x={0} y={0} width={area.ancho} height={area.fondo} />
        {children}
      </g>
    </svg>
  );
});

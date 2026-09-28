import type { Calculo } from "../tipos";
import { Plano } from "./Plano";

const NOMBRE = { normal: "Normal", cruzado: "Cruzado" } as const;

export function PisosDesdeArriba({ calculo, cajaAncho }: { calculo: Calculo; cajaAncho: number }) {
  const area = { ancho: calculo.resumen.area_ancho, fondo: calculo.resumen.area_profundidad };
  const esGirada = (ancho: number) => Math.abs(ancho - cajaAncho) > 1e-6;

  return (
    <div>
      <p className="leyenda-plantas">
        <i className="derecha" />caja derecha
        <i className="girada" />caja girada
      </p>
      <div className="plantas">
        {calculo.plantas
          .map((planta, i) => (
            <div className="planta" key={i}>
              <h3>
                Piso {i + 1} · {NOMBRE[planta.forma]} <small>{planta.cajas.length} cajas</small>
              </h3>
              <Plano area={area} margen={2} role="img" aria-label={`Piso ${i + 1} visto desde arriba`}>
                {planta.cajas.map((c, n) => (
                  <rect
                    key={n}
                    className={esGirada(c.ancho) ? "caja girada" : "caja"}
                    x={c.x}
                    y={c.y}
                    width={c.ancho}
                    height={c.profundidad}
                  />
                ))}
              </Plano>
            </div>
          ))
          .reverse()}
      </div>
    </div>
  );
}

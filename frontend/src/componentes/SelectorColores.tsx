import { COLOR_FORMA, MODOS, PALETA_PISOS, type Colores, type ModoColor } from "../logica/colores";
import { CARTON } from "../logica/modelos3d";

interface Props {
  colores: Colores;
  onCambiar: (colores: Colores) => void;
}

function Muestra({ color, texto }: { color: string; texto?: string }) {
  return (
    <span className="muestra">
      <i style={{ background: color }} />
      {texto}
    </span>
  );
}

/** Eleccion de los colores de las cajas en el 3D, con su leyenda. */
export function SelectorColores({ colores, onCambiar }: Props) {
  return (
    <div className="selector-colores">
      <label htmlFor="modo-color">Colores de las cajas</label>
      <select
        id="modo-color"
        value={colores.modo}
        onChange={(e) => onCambiar({ ...colores, modo: e.target.value as ModoColor })}
      >
        {MODOS.map((m) => (
          <option key={m.modo} value={m.modo}>{m.nombre}</option>
        ))}
      </select>

      {colores.modo === "uno" && (
        <input
          type="color"
          aria-label="Color de las cajas"
          value={colores.color}
          onChange={(e) => onCambiar({ ...colores, color: e.target.value })}
        />
      )}

      <span className="leyenda-colores">
        {colores.modo === "pisos" && (
          <>
            {PALETA_PISOS.map((c) => <Muestra key={c} color={c} />)}
            <span>piso 1, 2, 3... (pasa el raton para ver el numero)</span>
          </>
        )}
        {colores.modo === "forma" && (
          <>
            <Muestra color={COLOR_FORMA.normal} texto="normal" />
            <Muestra color={COLOR_FORMA.cruzado} texto="cruzado" />
          </>
        )}
        {colores.modo === "carton" && <Muestra color={CARTON} texto="como la caja real" />}
      </span>
    </div>
  );
}

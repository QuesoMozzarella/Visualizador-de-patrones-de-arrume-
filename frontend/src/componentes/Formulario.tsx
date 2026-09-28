import type { Forma, Medidas } from "../tipos";
import { segunRegla } from "../logica/pisos";

type Campo = keyof Omit<Medidas, "cruzar">;

interface Props {
  medidas: Medidas;
  pisos: Forma[];
  iguales: number;
  onCampo: (campo: Campo, valor: string) => void;
  onCruzar: (cruzar: boolean) => void;
  onPiso: (indice: number, forma: Forma) => void;
}

function Dato({ id, rotulo, valor, onCambio, min = 1, paso = 0.5, max }: {
  id: Campo;
  rotulo: string;
  valor: string;
  onCambio: (campo: Campo, valor: string) => void;
  min?: number;
  paso?: number;
  max?: number;
}) {
  return (
    <div className="dato">
      <label htmlFor={id}>{rotulo}</label>
      <input
        id={id}
        type="number"
        value={valor}
        min={min}
        max={max}
        step={paso}
        onChange={(e) => onCambio(id, e.target.value)}
      />
    </div>
  );
}

export function Formulario({ medidas, pisos, iguales, onCampo, onCruzar, onPiso }: Props) {
  const m = medidas;
  return (
    <>
      <fieldset>
        <legend>Pallet</legend>
        <div className="terna">
          <Dato id="pallet_ancho" rotulo="Ancho cm" valor={m.pallet_ancho} onCambio={onCampo} />
          <Dato id="pallet_profundidad" rotulo="Fondo cm" valor={m.pallet_profundidad} onCambio={onCampo} />
          <Dato id="pallet_alto" rotulo="Alto cm" valor={m.pallet_alto} onCambio={onCampo} />
        </div>
      </fieldset>

      <fieldset>
        <legend>Caja</legend>
        <div className="terna">
          <Dato id="caja_ancho" rotulo="Ancho cm" valor={m.caja_ancho} onCambio={onCampo} />
          <Dato id="caja_profundidad" rotulo="Fondo cm" valor={m.caja_profundidad} onCambio={onCampo} />
          <Dato id="caja_alto" rotulo="Alto cm" valor={m.caja_alto} onCambio={onCampo} />
        </div>
      </fieldset>

      <fieldset>
        <legend>Pisos</legend>
        <div className="par">
          <Dato id="niveles" rotulo="Cuantos" valor={m.niveles} onCambio={onCampo} paso={1} max={100} />
          {m.cruzar && (
            <Dato id="iguales" rotulo="Primeros normales" valor={m.iguales} onCambio={onCampo} paso={1} max={100} />
          )}
        </div>
        <label className="marcar">
          <input type="checkbox" checked={m.cruzar} onChange={(e) => onCruzar(e.target.checked)} />
          Cruzar pisos
        </label>
        <p className="nota-campo">
          Cruzado es el mismo acomodo con media vuelta. Los primeros van normales y desde el
          siguiente se turnan.
        </p>
        <ol className="pila">
          {pisos
            .map((forma, i) => (
              <li key={i} className={forma !== segunRegla(i, m.cruzar, iguales) ? "a-mano" : undefined}>
                <span className="n">{i + 1}</span>
                <select
                  aria-label={`Piso ${i + 1}`}
                  value={forma}
                  onChange={(e) => onPiso(i, e.target.value as Forma)}
                >
                  <option value="normal">Normal</option>
                  <option value="cruzado">Cruzado</option>
                </select>
              </li>
            ))
            .reverse()}
        </ol>
        <p className="nota-campo">Cambia el piso que quieras; los cambiados quedan marcados.</p>
      </fieldset>
    </>
  );
}

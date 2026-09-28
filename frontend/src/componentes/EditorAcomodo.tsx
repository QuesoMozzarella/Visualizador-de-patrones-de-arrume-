import { useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import {
  cubierto,
  desplazar,
  girar,
  malas,
  mover,
  poner,
  quitar,
} from "../logica/acomodo";
import type { Area, Caja2D } from "../tipos";
import { Plano } from "./Plano";

interface Props {
  area: Area;
  cajas: Caja2D[];
  aMano: boolean;
  /** Medidas de la caja derecha, para 'Poner caja' y para pintar las giradas. */
  caja: { ancho: number; fondo: number };
  onCambiar: (cajas: Caja2D[]) => void;
  onAutomatico: () => void;
}

interface Arrastre {
  i: number;
  dx: number;
  dy: number;
  inicio: Caja2D[];
  ultimo: Caja2D[] | null;
}

export function EditorAcomodo({ area, cajas, aMano, caja, onCambiar, onAutomatico }: Props) {
  const grupo = useRef<SVGGElement>(null);
  const [elegida, setElegida] = useState<number | null>(null);
  const [sinHueco, setSinHueco] = useState(false);
  // Mientras se arrastra se dibuja aqui; al soltar se avisa una sola vez
  const [enVivo, setEnVivo] = useState<Caja2D[] | null>(null);
  const arrastre = useRef<Arrastre | null>(null);

  const visibles = enVivo ?? cajas;
  const marcadas = malas(visibles, area);
  const sel = elegida !== null && elegida < visibles.length ? elegida : null;

  function cambiar(nuevas: Caja2D[], nuevaElegida: number | null = sel) {
    setSinHueco(false);
    setElegida(nuevaElegida);
    onCambiar(nuevas);
  }

  function punto(evento: PointerEvent): { x: number; y: number } {
    const matriz = grupo.current!.getScreenCTM()!.inverse();
    const p = new DOMPoint(evento.clientX, evento.clientY).matrixTransform(matriz);
    return { x: p.x, y: p.y };
  }

  function alApretar(evento: PointerEvent<SVGSVGElement>) {
    evento.currentTarget.focus();
    const rect = (evento.target as Element).closest("[data-i]");
    if (!rect) {
      setElegida(null);
      return;
    }
    const i = Number(rect.getAttribute("data-i"));
    const p = punto(evento);
    arrastre.current = { i, dx: p.x - cajas[i].x, dy: p.y - cajas[i].y, inicio: cajas, ultimo: null };
    evento.currentTarget.setPointerCapture(evento.pointerId);
    setElegida(i);
  }

  function alMover(evento: PointerEvent<SVGSVGElement>) {
    const a = arrastre.current;
    if (!a) return;
    // Sin el boton apretado ya no se arrastra, aunque se perdiera el soltar
    if (!(evento.buttons & 1)) {
      soltar();
      return;
    }
    const p = punto(evento);
    a.ultimo = mover(a.inicio, a.i, p.x - a.dx, p.y - a.dy, area);
    setEnVivo(a.ultimo);
  }

  function soltar() {
    const a = arrastre.current;
    arrastre.current = null;
    if (a?.ultimo) cambiar(a.ultimo, a.i);
    setEnVivo(null);
  }

  function alTeclado(evento: KeyboardEvent<SVGSVGElement>) {
    if (sel === null) return;
    const paso = evento.shiftKey ? 10 : 1;
    const flechas: Record<string, [number, number]> = {
      ArrowLeft: [-paso, 0],
      ArrowRight: [paso, 0],
      ArrowUp: [0, paso],
      ArrowDown: [0, -paso],
    };
    if (flechas[evento.key]) {
      cambiar(desplazar(cajas, sel, ...flechas[evento.key]));
    } else if (evento.key === "r" || evento.key === "R") {
      cambiar(girar(cajas, sel, area));
    } else if (evento.key === "Delete" || evento.key === "Backspace") {
      cambiar(quitar(cajas, sel), null);
    } else {
      return;
    }
    evento.preventDefault();
  }

  function alPoner() {
    const nuevas = poner(cajas, caja.ancho, caja.fondo, area);
    if (!nuevas) {
      setSinHueco(true);
      return;
    }
    cambiar(nuevas, nuevas.length - 1);
  }

  const esGirada = (c: Caja2D) => Math.abs(c.ancho - caja.ancho) > 1e-6;

  return (
    <div className="editor">
      <div className="herramientas">
        <button type="button" onClick={alPoner}>Poner caja</button>
        <button type="button" disabled={sel === null} onClick={() => sel !== null && cambiar(girar(cajas, sel, area))}>
          Girar
        </button>
        <button type="button" disabled={sel === null} onClick={() => sel !== null && cambiar(quitar(cajas, sel), null)}>
          Quitar
        </button>
        <button type="button" onClick={() => cambiar([], null)}>Vaciar</button>
        <span className="hueco" />
        <span className="estado-acomodo">{aMano ? "acomodado a mano" : "acomodo automatico"}</span>
        <button type="button" disabled={!aMano} onClick={() => { setElegida(null); onAutomatico(); }}>
          Acomodo automatico
        </button>
      </div>

      <Plano
        ref={grupo}
        area={area}
        id="plano"
        tabIndex={0}
        role="img"
        aria-label="Acomodo del nivel visto desde arriba; arrastra las cajas"
        onPointerDown={alApretar}
        onPointerMove={alMover}
        onPointerUp={soltar}
        onPointerCancel={soltar}
        onLostPointerCapture={soltar}
        onKeyDown={alTeclado}
      >
        {visibles.map((c, i) => (
          <rect
            key={i}
            data-i={i}
            x={c.x}
            y={c.y}
            width={c.ancho}
            height={c.profundidad}
            className={[
              "caja",
              esGirada(c) && "girada",
              marcadas.has(i) && "choca",
              sel === i && "elegida",
            ].filter(Boolean).join(" ")}
          />
        ))}
      </Plano>

      <div className="pie-plano">
        <b>{visibles.length} cajas</b> &nbsp; {cubierto(visibles, area).toFixed(1)} % del pallet cubierto &nbsp;{" "}
        {sinHueco ? (
          <span className="mal">No queda hueco para otra caja.</span>
        ) : marcadas.size ? (
          <span className="mal">{marcadas.size} marcadas en rojo: se pisan o se salen</span>
        ) : (
          "todo dentro y sin pisarse"
        )}
      </div>
      <p className="ayuda">
        Arrastra las cajas; se pegan solas a los bordes y a las otras cajas. Con una elegida:{" "}
        <kbd>flechas</kbd> la mueven 1 cm (<kbd>Shift</kbd> 10 cm), <kbd>R</kbd> la gira,{" "}
        <kbd>Supr</kbd> la quita.
      </p>
    </div>
  );
}

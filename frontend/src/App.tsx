import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { api, ErrorApi, pedirInforme } from "./api";
import { Avisos, Cifras } from "./componentes/Cifras";
import { EditorAcomodo } from "./componentes/EditorAcomodo";
import { Formulario } from "./componentes/Formulario";
import { Guardados } from "./componentes/Guardados";
import { PisosDesdeArriba } from "./componentes/PisosDesdeArriba";
import { SelectorColores } from "./componentes/SelectorColores";
import { coloresGuardados, guardarColores, type Colores } from "./logica/colores";
import { imagenesInforme } from "./logica/imagen3d";
import { ajustar, entero, MAXIMO_PISOS, reparto } from "./logica/pisos";
import type { Caja2D, Calculo, Datos, Forma, Guardado, GuardadoCompleto, Medidas } from "./tipos";

// Plotly pesa varios MB: se descarga aparte, sin frenar la primera pintura
const Vista3D = lazy(() => import("./componentes/Vista3D"));
const CajaYPallet = lazy(() => import("./componentes/CajaYPallet"));

type Vista = "acomodo" | "3d" | "pisos" | "modelos";

interface Acomodo {
  cajas: Caja2D[];
  /** false mientras sea el que calcula el programa. */
  aMano: boolean;
}

const CAMPOS: (keyof Omit<Medidas, "cruzar">)[] = [
  "pallet_ancho", "pallet_profundidad", "pallet_alto",
  "caja_ancho", "caja_profundidad", "caja_alto",
  "niveles", "iguales",
];

// Cambiar el pallet o la caja deshace lo acomodado: ya no son esas cajas
const REHACEN = ["pallet_ancho", "pallet_profundidad", "caja_ancho", "caja_profundidad"];

const AUTOMATICO: Acomodo = { cajas: [], aMano: false };

function medidasDe(valores: Record<string, unknown>, base?: Medidas): Medidas {
  const m = {} as Medidas;
  for (const campo of CAMPOS) {
    const v = valores[campo] ?? base?.[campo];
    m[campo] = v === undefined || v === null ? "" : String(v);
  }
  m.cruzar = typeof valores.cruzar === "boolean" ? valores.cruzar : (base?.cruzar ?? true);
  if (!m.iguales) m.iguales = "1";
  return m;
}

export function App() {
  const [inicial, setInicial] = useState<Medidas | null>(null);
  const [medidas, setMedidas] = useState<Medidas | null>(null);
  const [pisos, setPisos] = useState<Forma[]>([]);
  const [acomodo, setAcomodo] = useState<Acomodo>(AUTOMATICO);
  const [calculo, setCalculo] = useState<Calculo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [vista, setVista] = useState<Vista>("3d");
  const [actual, setActual] = useState<Guardado | null>(null);
  const [copiado, setCopiado] = useState<string | null>(null);
  const [informePdf, setInformePdf] = useState<{ texto: string; malo: boolean } | null>(null);
  const [generando, setGenerando] = useState(false);
  const [colores, setColores] = useState<Colores>(coloresGuardados);

  const niveles = medidas ? (entero(medidas.niveles, 1, MAXIMO_PISOS) ?? 0) : 0;
  const iguales = medidas ? (entero(medidas.iguales, 1, MAXIMO_PISOS) ?? 1) : 1;

  // ---- Arranque: los valores iniciales los dice el backend ------------------
  useEffect(() => {
    api
      .valoresIniciales()
      .then((valores) => {
        const m = medidasDe(valores);
        setInicial(m);
        setMedidas(m);
        setPisos(reparto(entero(m.niveles, 1, MAXIMO_PISOS) ?? 0, m.cruzar, entero(m.iguales, 1, MAXIMO_PISOS) ?? 1));
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const datos = useCallback((): Datos => {
    return {
      ...medidas!,
      pisos,
      ...(acomodo.aMano ? { acomodo: acomodo.cajas } : {}),
    };
  }, [medidas, pisos, acomodo]);

  // ---- Calcular cada vez que algo cambia (con una pausa corta) -------------
  const pedido = useRef<AbortController | null>(null);
  const cajasEnviadas = acomodo.aMano ? acomodo.cajas : null;

  useEffect(() => {
    if (!medidas) return;
    const cuerpo = datos();
    const espera = setTimeout(() => {
      pedido.current?.abort();
      const control = new AbortController();
      pedido.current = control;
      api
        .calcular(cuerpo, control.signal)
        .then((r) => {
          if (!r.ok) {
            setError(r.error);
            return;
          }
          setError(null);
          setCalculo(r);
          // Si el usuario no ha tocado el acomodo, el editor parte del calculado
          setAcomodo((antes) => (antes.aMano ? antes : { cajas: r.acomodo, aMano: false }));
        })
        .catch((e) => {
          if (e instanceof ErrorApi) setError(e.message);
        });
    }, 250);
    return () => clearTimeout(espera);
    // 'datos' se lee dentro; lo que decide recalcular son estas tres cosas
  }, [medidas, pisos, cajasEnviadas]);

  if (!medidas || !inicial) {
    return (
      <main className="cargando">
        {error ? <Avisos avisos={[]} error={error} /> : <p>Abriendo Arrume...</p>}
      </main>
    );
  }

  // ---- Cambios del formulario ---------------------------------------------
  function alCampo(campo: keyof Omit<Medidas, "cruzar">, valor: string) {
    const m = { ...medidas!, [campo]: valor };
    setMedidas(m);
    if (REHACEN.includes(campo)) setAcomodo(AUTOMATICO);
    if (campo === "niveles") {
      setPisos((p) => ajustar(p, entero(valor, 1, MAXIMO_PISOS) ?? 0, m.cruzar, iguales));
    }
    if (campo === "iguales") {
      setPisos(reparto(niveles, m.cruzar, entero(valor, 1, MAXIMO_PISOS) ?? 1));
    }
  }

  function alCruzar(cruzar: boolean) {
    setMedidas({ ...medidas!, cruzar });
    setPisos(reparto(niveles, cruzar, iguales));
  }

  function alPiso(indice: number, forma: Forma) {
    setPisos((p) => p.map((f, i) => (i === indice ? forma : f)));
  }

  function abrir(guardado: GuardadoCompleto) {
    const d = guardado.datos;
    const m = medidasDe(d, inicial!);
    setMedidas(m);
    const n = entero(m.niveles, 1, MAXIMO_PISOS) ?? 0;
    setPisos(
      Array.isArray(d.pisos) && d.pisos.length === n
        ? (d.pisos as Forma[])
        : reparto(n, m.cruzar, entero(m.iguales, 1, MAXIMO_PISOS) ?? 1),
    );
    setAcomodo(Array.isArray(d.acomodo) ? { cajas: d.acomodo as Caja2D[], aMano: true } : AUTOMATICO);
    setActual(guardado);
  }

  function restablecer() {
    setMedidas(inicial!);
    setPisos(reparto(entero(inicial!.niveles, 1, MAXIMO_PISOS) ?? 0, inicial!.cruzar, 1));
    setAcomodo(AUTOMATICO);
    setActual(null);
  }

  async function descargarInforme() {
    if (!calculo) return;
    setGenerando(true);
    setInformePdf(null);
    try {
      const imagenes = await imagenesInforme(calculo, medidasCaja, colores);
      const { pdf, archivo } = await pedirInforme({
        datos: datos(),
        nombre: actual?.nombre ?? "",
        ...imagenes,
      });
      const enlace = document.createElement("a");
      enlace.href = URL.createObjectURL(pdf);
      enlace.download = archivo;
      enlace.click();
      setTimeout(() => URL.revokeObjectURL(enlace.href), 10_000);
      setInformePdf({ texto: `Descargado: ${archivo}`, malo: false });
    } catch (e) {
      if (!(e instanceof ErrorApi)) throw e;
      setInformePdf({ texto: e.message, malo: true });
    } finally {
      setGenerando(false);
    }
  }

  async function copiarInforme() {
    if (!calculo) return;
    try {
      await navigator.clipboard.writeText(calculo.texto);
      setCopiado("Informe copiado");
    } catch {
      setCopiado("No se pudo copiar");
    }
    setTimeout(() => setCopiado(null), 1600);
  }

  const area = calculo
    ? { ancho: calculo.resumen.area_ancho, fondo: calculo.resumen.area_profundidad }
    : null;
  const caja = { ancho: Number(medidas.caja_ancho), fondo: Number(medidas.caja_profundidad) };
  const medidasCaja: [number, number, number] = [
    Number(medidas.caja_ancho), Number(medidas.caja_profundidad), Number(medidas.caja_alto),
  ];
  const medidasPallet: [number, number, number] = [
    Number(medidas.pallet_ancho), Number(medidas.pallet_profundidad), Number(medidas.pallet_alto),
  ];

  return (
    <>
      <header className="franja">
        <div className="marca">Arrume</div>
        <div className="ficha-titulo">
          <span><i>pallet</i>{[medidas.pallet_ancho, medidas.pallet_profundidad, medidas.pallet_alto].map((v) => v || "?").join(" × ")}</span>
          <span><i>caja</i>{[medidas.caja_ancho, medidas.caja_profundidad, medidas.caja_alto].map((v) => v || "?").join(" × ")}</span>
          {actual && <span><i>guardado</i>{actual.nombre}</span>}
        </div>
      </header>

      <main className="taller">
        <div className="columna">
        <form className="medidas" autoComplete="off" onSubmit={(e) => e.preventDefault()}>
          <Formulario
            medidas={medidas}
            pisos={pisos}
            iguales={iguales}
            onCampo={alCampo}
            onCruzar={alCruzar}
            onPiso={alPiso}
          />
          <div className="mandos">
            <button
              type="button"
              className="calcular"
              onClick={() => void descargarInforme()}
              disabled={!calculo || !!error || generando}
            >
              {generando ? "Armando el PDF..." : "Informe PDF"}
            </button>
            {informePdf && (
              <p className={informePdf.malo ? "mensaje malo" : "mensaje"} role="status">
                {informePdf.texto}
              </p>
            )}
            <div className="fila-mandos">
              <button type="button" onClick={() => void copiarInforme()} disabled={!calculo}>
                {copiado ?? "Copiar informe"}
              </button>
              <button type="button" onClick={restablecer}>Medidas base</button>
            </div>
          </div>
        </form>
        <div className="medidas">
          <Guardados actual={actual} datos={datos} onAbrir={abrir} onGuardado={setActual} />
        </div>
        </div>

        <section className={error ? "carga viejo" : "carga"}>
          <Avisos avisos={error ? [] : (calculo?.avisos ?? [])} error={error} />

          <div className="vistas" role="tablist">
            {([
              ["acomodo", "Acomodo del nivel"],
              ["3d", "Arrume"],
              ["pisos", "Pisos desde arriba"],
              ["modelos", "Caja y pallet"],
            ] as [Vista, string][]).map(([clave, rotulo]) => (
              <button
                key={clave}
                type="button"
                role="tab"
                className="pestana"
                aria-selected={vista === clave}
                aria-pressed={vista === clave}
                onClick={() => setVista(clave)}
              >
                {rotulo}
              </button>
            ))}
          </div>

          {vista === "acomodo" && area && (
            <EditorAcomodo
              area={area}
              cajas={acomodo.cajas}
              aMano={acomodo.aMano}
              caja={caja}
              onCambiar={(cajas) => setAcomodo({ cajas, aMano: true })}
              onAutomatico={() => setAcomodo(AUTOMATICO)}
            />
          )}
          {vista === "3d" && (
            <SelectorColores
              colores={colores}
              onCambiar={(nuevos) => {
                setColores(nuevos);
                guardarColores(nuevos);
              }}
            />
          )}
          {calculo && (
            <Suspense fallback={vista === "3d" ? <div id="arrume" className="cargando">Cargando el 3D...</div> : null}>
              <Vista3D calculo={calculo} visible={vista === "3d"} colores={colores} />
            </Suspense>
          )}
          {vista === "pisos" && calculo && (
            <PisosDesdeArriba calculo={calculo} cajaAncho={caja.ancho} />
          )}
          {vista === "modelos" && (
            <Suspense fallback={<p className="cargando">Cargando el 3D...</p>}>
              <CajaYPallet caja={medidasCaja} pallet={medidasPallet} />
            </Suspense>
          )}

          {calculo && <Cifras r={calculo.resumen} />}
        </section>
      </main>
    </>
  );
}

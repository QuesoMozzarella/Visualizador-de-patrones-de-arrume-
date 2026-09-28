import { useEffect, useState } from "react";
import { api, ErrorApi } from "../api";
import type { Datos, Guardado, GuardadoCompleto } from "../tipos";

interface Props {
  /** El guardado que esta abierto, si hay uno. */
  actual: Guardado | null;
  datos: () => Datos;
  onAbrir: (guardado: GuardadoCompleto) => void;
  onGuardado: (guardado: Guardado | null) => void;
}

const fecha = new Intl.DateTimeFormat("es", { dateStyle: "short", timeStyle: "short" });

export function Guardados({ actual, datos, onAbrir, onGuardado }: Props) {
  const [lista, setLista] = useState<Guardado[]>([]);
  const [nombre, setNombre] = useState("");
  const [mensaje, setMensaje] = useState<{ texto: string; malo: boolean } | null>(null);
  const [borrando, setBorrando] = useState<number | null>(null);
  const [ocupado, setOcupado] = useState(false);

  async function recargar() {
    try {
      setLista(await api.listar());
    } catch (error) {
      setMensaje({ texto: (error as Error).message, malo: true });
    }
  }

  useEffect(() => {
    void recargar();
  }, []);

  useEffect(() => {
    setNombre(actual?.nombre ?? "");
  }, [actual]);

  async function hacer(accion: () => Promise<void>, exito: string) {
    setOcupado(true);
    setMensaje(null);
    try {
      await accion();
      setMensaje({ texto: exito, malo: false });
      await recargar();
    } catch (error) {
      if (!(error instanceof ErrorApi)) throw error;
      setMensaje({ texto: error.message, malo: true });
    } finally {
      setOcupado(false);
    }
  }

  const guardar = (comoNuevo: boolean) =>
    hacer(async () => {
      const guardado =
        actual && !comoNuevo
          ? await api.actualizar(actual.id, nombre, datos())
          : await api.crear(nombre, datos());
      onGuardado(guardado);
    }, "Guardado.");

  const abrir = (id: number) =>
    hacer(async () => {
      onAbrir(await api.abrir(id));
    }, "Abierto.");

  const borrar = (id: number) =>
    hacer(async () => {
      await api.borrar(id);
      setBorrando(null);
      if (actual?.id === id) onGuardado(null);
    }, "Borrado.");

  return (
    <fieldset className="guardados">
      <legend>Guardados</legend>
      <form
        className="guardar"
        onSubmit={(e) => {
          e.preventDefault();
          void guardar(false);
        }}
      >
        <input
          aria-label="Nombre del arrume"
          placeholder="Nombre, p. ej. Galletas 40x30"
          value={nombre}
          maxLength={100}
          onChange={(e) => setNombre(e.target.value)}
        />
        <div className="fila-mandos">
          <button type="submit" disabled={ocupado}>
            {actual ? "Guardar cambios" : "Guardar"}
          </button>
          {actual && (
            <button type="button" disabled={ocupado} onClick={() => void guardar(true)}>
              Guardar como nuevo
            </button>
          )}
        </div>
      </form>
      {mensaje && (
        <p className={mensaje.malo ? "mensaje malo" : "mensaje"} role="status">
          {mensaje.texto}
        </p>
      )}

      {lista.length === 0 ? (
        <p className="nota-campo">Todavia no hay arrumes guardados.</p>
      ) : (
        <ul className="lista-guardados">
          {lista.map((g) => (
            <li key={g.id} className={actual?.id === g.id ? "abierto" : undefined}>
              <div className="guardado-nombre">
                <b>{g.nombre}</b>
                <small>{fecha.format(new Date(g.actualizado))}</small>
              </div>
              {borrando === g.id ? (
                <div className="acciones">
                  <span>¿Borrar?</span>
                  <button type="button" className="peligro" disabled={ocupado} onClick={() => void borrar(g.id)}>
                    Si
                  </button>
                  <button type="button" onClick={() => setBorrando(null)}>No</button>
                </div>
              ) : (
                <div className="acciones">
                  <button type="button" disabled={ocupado} onClick={() => void abrir(g.id)}>Abrir</button>
                  <button type="button" onClick={() => setBorrando(g.id)}>Borrar</button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </fieldset>
  );
}

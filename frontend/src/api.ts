// Cliente de la API Flask. Todas las llamadas pasan por aqui.

import type { Datos, Guardado, GuardadoCompleto, RespuestaCalculo } from "./tipos";

// Vacio = mismo origen: en desarrollo lo reenvia Vite, en produccion lo
// sirve Flask. Para un backend en otro sitio: VITE_API=https://... al compilar.
const BASE = import.meta.env.VITE_API ?? "";

export class ErrorApi extends Error {}

async function pedir<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(BASE + ruta, {
      ...opciones,
      headers: { "Content-Type": "application/json", ...opciones.headers },
    });
  } catch (error) {
    // Un calculo que se cancelo porque llego otro mas nuevo no es un fallo
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ErrorApi("No hay conexion con el programa. Revisa que el backend este abierto.");
  }
  if (respuesta.status === 204) return undefined as T;
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    throw new ErrorApi(cuerpo?.error ?? `El programa respondio ${respuesta.status}.`);
  }
  return cuerpo as T;
}

export const api = {
  valoresIniciales: () => pedir<Record<string, unknown>>("/api/valores-iniciales"),

  calcular: (datos: Datos, senal?: AbortSignal) =>
    pedir<RespuestaCalculo>("/api/calcular", {
      method: "POST",
      body: JSON.stringify(datos),
      signal: senal,
    }),

  listar: () => pedir<Guardado[]>("/api/arrumes"),

  abrir: (id: number) => pedir<GuardadoCompleto>(`/api/arrumes/${id}`),

  crear: (nombre: string, datos: Datos) =>
    pedir<GuardadoCompleto>("/api/arrumes", {
      method: "POST",
      body: JSON.stringify({ nombre, datos }),
    }),

  actualizar: (id: number, nombre: string, datos: Datos) =>
    pedir<GuardadoCompleto>(`/api/arrumes/${id}`, {
      method: "PUT",
      body: JSON.stringify({ nombre, datos }),
    }),

  borrar: (id: number) => pedir<void>(`/api/arrumes/${id}`, { method: "DELETE" }),
};

/** El informe en PDF y el nombre con que lo sugiere el backend. */
export async function pedirInforme(cuerpo: {
  datos: Datos;
  nombre?: string;
  imagen_3d?: string;
  imagen_caja?: string;
  imagen_pallet?: string;
}): Promise<{ pdf: Blob; archivo: string }> {
  let respuesta: Response;
  try {
    respuesta = await fetch(BASE + "/api/informe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo),
    });
  } catch {
    throw new ErrorApi("No hay conexion con el programa. Revisa que el backend este abierto.");
  }
  if (!respuesta.ok) {
    const error = await respuesta.json().catch(() => null);
    throw new ErrorApi(error?.error ?? `El programa respondio ${respuesta.status}.`);
  }
  const disposicion = respuesta.headers.get("Content-Disposition") ?? "";
  const archivo = /filename="([^"]+)"/.exec(disposicion)?.[1] ?? "arrume.pdf";
  return { pdf: await respuesta.blob(), archivo };
}

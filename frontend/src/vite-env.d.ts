/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Direccion del backend si no esta en el mismo origen, p. ej. https://api.ejemplo.com */
  readonly VITE_API?: string;
}

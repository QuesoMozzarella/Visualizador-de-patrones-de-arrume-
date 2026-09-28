// Lo que viaja entre el frontend y la API. Los nombres de los campos son
// los del backend (arrume_api/servicio.py), para no traducir dos veces.

export type Forma = "normal" | "cruzado";

/** Una caja de un nivel vista desde arriba, en cm. */
export interface Caja2D {
  x: number;
  y: number;
  ancho: number;
  profundidad: number;
}

/** Una caja del arrume en el espacio, en cm. 'nivel' empieza en 0. */
export interface Caja3D extends Caja2D {
  z: number;
  alto: number;
  nivel: number;
}

/** Los campos del formulario tal como estan en los inputs: texto. */
export interface Medidas {
  pallet_ancho: string;
  pallet_profundidad: string;
  pallet_alto: string;
  caja_ancho: string;
  caja_profundidad: string;
  caja_alto: string;
  niveles: string;
  iguales: string;
  cruzar: boolean;
}

/** Lo que se manda a calcular y lo que se guarda. */
export interface Datos extends Medidas {
  pisos: Forma[];
  acomodo?: Caja2D[];
}

export interface Resumen {
  cajas_por_nivel: number;
  cajas_normales: number;
  cajas_giradas: number;
  niveles: number;
  total_cajas: number;
  altura_total: number;
  aprovechamiento: number;
  intercalado: boolean;
  area_ancho: number;
  area_profundidad: number;
}

export interface Planta {
  forma: Forma;
  cajas: Caja2D[];
}

export interface Calculo {
  ok: true;
  pallet: { ancho: number; profundidad: number; alto: number };
  cajas: Caja3D[];
  resumen: Resumen;
  avisos: string[];
  texto: string;
  acomodo: Caja2D[];
  plantas: Planta[];
}

export type RespuestaCalculo = Calculo | { ok: false; error: string };

export interface Guardado {
  id: number;
  nombre: string;
  creado: string;
  actualizado: string;
}

export interface GuardadoCompleto extends Guardado {
  datos: Partial<Omit<Datos, keyof Medidas>> & Record<string, unknown>;
}

export interface Area {
  ancho: number;
  fondo: number;
}

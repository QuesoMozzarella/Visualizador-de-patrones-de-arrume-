import { describe, expect, it } from "vitest";
import type { Cuerpo } from "./malla3d";
import { cotas, figuraCaja, figuraPallet, piezasCaja, piezasPallet } from "./modelos3d";

const arriba = (c: Cuerpo) => c[2] + c[5];
const TOL = 1e-9;

describe("pallet", () => {
  const piezas = piezasPallet(120, 100, 15);

  it("la cara de arriba queda justo al alto del pallet", () => {
    expect(Math.max(...piezas.map(arriba))).toBeCloseTo(15);
    expect(Math.min(...piezas.map((c) => c[2]))).toBe(0);
  });

  it("ninguna pieza se sale del pallet", () => {
    for (const [x, y, , dx, dy] of piezas) {
      expect(x).toBeGreaterThanOrEqual(-TOL);
      expect(y).toBeGreaterThanOrEqual(-TOL);
      expect(x + dx).toBeLessThanOrEqual(120 + TOL);
      expect(y + dy).toBeLessThanOrEqual(100 + TOL);
    }
  });

  it("tiene tablas abajo, nueve tacos, tres travesanos y tablas arriba", () => {
    const tacos = piezas.filter((c) => c[2] > 0 && arriba(c) < 15 - 2.5 - TOL && c[5] > 3);
    expect(tacos).toHaveLength(9);
    const deArriba = piezas.filter((c) => Math.abs(arriba(c) - 15) < TOL);
    expect(deArriba.length).toBeGreaterThanOrEqual(3);
    // Las tablas de arriba cubren de borde a borde en el fondo
    expect(Math.min(...deArriba.map((c) => c[1]))).toBe(0);
    expect(Math.max(...deArriba.map((c) => c[1] + c[4]))).toBeCloseTo(100);
  });

  it("se adapta a otras medidas", () => {
    const grande = piezasPallet(200, 150, 20);
    expect(Math.max(...grande.map(arriba))).toBeCloseTo(20);
    expect(Math.max(...grande.map((c) => c[0] + c[3]))).toBeCloseTo(200);
  });

  it("un pallet muy delgado es una plancha", () => {
    expect(piezasPallet(120, 100, 3)).toEqual([[0, 0, 0, 120, 100, 3]]);
  });
});

describe("caja", () => {
  it("mide lo que se pide y la cinta va encima, centrada", () => {
    const { caja, cinta } = piezasCaja(40, 30, 25);
    expect(caja).toEqual([0, 0, 0, 40, 30, 25]);
    expect(cinta[2]).toBe(25);
    expect(cinta[1] + cinta[4] / 2).toBeCloseTo(15);
    expect(cinta[3]).toBe(40);
  });
});

describe("cotas", () => {
  it("rotulan las tres medidas", () => {
    const textos = cotas(40, 30, 25).rotulos.map((r) => r.text);
    expect(textos).toEqual(["ancho 40 cm", "fondo 30 cm", "alto 25 cm"]);
  });

  it("respetan los decimales", () => {
    expect(cotas(37.5, 27.5, 22).rotulos[0].text).toBe("ancho 37.5 cm");
  });

  it("las figuras llevan las cotas en la escena", () => {
    for (const f of [figuraCaja(40, 30, 25), figuraPallet(120, 100, 15)]) {
      expect(f.layout.scene.annotations).toHaveLength(3);
    }
  });
});

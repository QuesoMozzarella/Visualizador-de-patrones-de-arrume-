import { describe, expect, it } from "vitest";
import { cubierto, girar, hueco, imantar, malas, mover, poner, quitar } from "./acomodo";
import type { Caja2D } from "../tipos";

const AREA = { ancho: 120, fondo: 100 };
const caja = (x: number, y: number, ancho = 40, profundidad = 30): Caja2D => ({ x, y, ancho, profundidad });

describe("cajas que estan mal", () => {
  it("marca las dos cajas que se pisan", () => {
    expect([...malas([caja(0, 0), caja(20, 0), caja(80, 0)], AREA)]).toEqual([0, 1]);
  });

  it("marca la que se sale del pallet", () => {
    expect([...malas([caja(90, 0)], AREA)]).toEqual([0]);
  });

  it("dos cajas que solo se tocan no se pisan", () => {
    expect(malas([caja(0, 0), caja(40, 0)], AREA).size).toBe(0);
  });
});

describe("imanes", () => {
  it("se pega al candidato cercano", () => {
    expect(imantar(38.8, [0, 40, 80], 2)).toBe(40);
  });

  it("no se pega si esta lejos", () => {
    expect(imantar(35, [0, 40, 80], 2)).toBe(35);
  });

  it("al mover, la caja se pega al borde de la vecina", () => {
    const cajas = mover([caja(0, 0), caja(60, 50)], 1, 41.2, 50.4, AREA);
    expect(cajas[1]).toEqual(caja(40, 50));
  });

  it("sin nada cerca redondea al cm", () => {
    const cajas = mover([caja(0, 0), caja(60, 50)], 1, 55.4, 45.6, AREA);
    expect(cajas[1]).toEqual(caja(55, 46));
  });

  it("no modifica la lista que recibe", () => {
    const original = [caja(0, 0), caja(60, 50)];
    mover(original, 1, 10, 10, AREA);
    expect(original[1]).toEqual(caja(60, 50));
  });
});

describe("herramientas", () => {
  it("girar intercambia las medidas y la mete si se sale", () => {
    expect(girar([caja(80, 70)], 0, AREA)[0]).toEqual(caja(80, 60, 30, 40));
  });

  it("quitar saca solo esa caja", () => {
    expect(quitar([caja(0, 0), caja(40, 0)], 0)).toEqual([caja(40, 0)]);
  });

  it("el hueco es el primero libre de abajo arriba", () => {
    expect(hueco([caja(0, 0), caja(40, 0), caja(80, 0)], 40, 30, AREA)).toEqual(caja(0, 30));
  });

  it("poner prueba la caja girada si derecha no cabe", () => {
    // Queda una franja de 30 de ancho y 100 de fondo a la derecha
    const lleno = [caja(0, 0, 90, 100)];
    expect(poner(lleno, 40, 30, AREA)).toEqual([...lleno, caja(90, 0, 30, 40)]);
  });

  it("poner devuelve null si no cabe de ninguna forma", () => {
    expect(poner([caja(0, 0, 120, 100)], 40, 30, AREA)).toBeNull();
  });

  it("cubierto es el porcentaje del pallet", () => {
    expect(cubierto([caja(0, 0, 60, 100)], AREA)).toBe(50);
  });
});

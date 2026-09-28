import { describe, expect, it } from "vitest";
import { COLOR_FORMA, colorDePiso, PALETA_PISOS } from "./colores";
import { figura } from "./figura3d";
import { CARTON } from "./modelos3d";

describe("color de cada piso", () => {
  it("un color por piso, en orden, y vuelve a empezar despues del octavo", () => {
    const colores = { modo: "pisos" as const, color: "#000000" };
    expect([0, 1, 7, 8].map((n) => colorDePiso(n, "normal", colores))).toEqual([
      PALETA_PISOS[0], PALETA_PISOS[1], PALETA_PISOS[7], PALETA_PISOS[0],
    ]);
  });

  it("dos pisos seguidos nunca llevan el mismo color", () => {
    const colores = { modo: "pisos" as const, color: "#000000" };
    for (let n = 0; n < 30; n++) {
      expect(colorDePiso(n, "normal", colores)).not.toBe(colorDePiso(n + 1, "normal", colores));
    }
  });

  it("normal y cruzado se pintan segun la forma, no segun el piso", () => {
    const colores = { modo: "forma" as const, color: "#000000" };
    expect(colorDePiso(0, "normal", colores)).toBe(COLOR_FORMA.normal);
    expect(colorDePiso(5, "cruzado", colores)).toBe(COLOR_FORMA.cruzado);
  });

  it("carton pinta todo del color de la caja", () => {
    expect(colorDePiso(3, "cruzado", { modo: "carton", color: "#000000" })).toBe(CARTON);
  });

  it("un solo color usa el elegido, y si no es valido el inicial", () => {
    expect(colorDePiso(2, "normal", { modo: "uno", color: "#123abc" })).toBe("#123abc");
    expect(colorDePiso(2, "normal", { modo: "uno", color: "rojo" })).toBe("#2a78d6");
  });
});

describe("la figura del arrume usa los colores elegidos", () => {
  const cajas = [0, 1].map((nivel) => ({
    x: 0, y: 0, z: 15 + 25 * nivel, ancho: 40, profundidad: 30, alto: 25, nivel,
  }));
  const pallet = { ancho: 120, profundidad: 100, alto: 15 };

  it("un volumen por piso con su color", () => {
    const { data } = figura(pallet, cajas, ["normal", "cruzado"], { modo: "forma", color: "#000000" });
    const pisos = data.filter((t) => (t as { name?: string }).name?.startsWith("Piso"));
    expect(pisos.map((t) => (t as { color: string }).color)).toEqual([
      COLOR_FORMA.normal, COLOR_FORMA.cruzado,
    ]);
  });
});

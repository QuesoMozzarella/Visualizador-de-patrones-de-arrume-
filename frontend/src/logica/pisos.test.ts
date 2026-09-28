import { describe, expect, it } from "vitest";
import { ajustar, entero, reparto, segunRegla } from "./pisos";

const letras = (pisos: string[]) => pisos.map((f) => f[0].toUpperCase()).join("");

describe("reparto de pisos", () => {
  it.each([
    [1, "NCNCNC"],
    [2, "NNCNCN"],
    [3, "NNNCNC"],
    [6, "NNNNNN"],
  ])("con %i primeros normales queda %s", (iguales, esperado) => {
    expect(letras(reparto(6, true, iguales))).toBe(esperado);
  });

  it("sin cruzar todos van normales", () => {
    expect(letras(reparto(4, false, 2))).toBe("NNNN");
  });

  it("coincide con la regla piso por piso", () => {
    expect(reparto(5, true, 2)).toEqual([0, 1, 2, 3, 4].map((i) => segunRegla(i, true, 2)));
  });
});

describe("ajustar la cantidad de pisos", () => {
  it("conserva los que ya estaban elegidos", () => {
    const elegidos = ["cruzado", "cruzado"] as const;
    expect(ajustar([...elegidos], 4, true, 1)).toEqual(["cruzado", "cruzado", "normal", "cruzado"]);
  });

  it("recorta si hay menos pisos", () => {
    expect(ajustar(reparto(5, true, 1), 2, true, 1)).toEqual(["normal", "cruzado"]);
  });
});

describe("entero", () => {
  it.each([
    ["5", 5],
    ["2.6", 3],
    ["", null],
    ["0", null],
    ["abc", null],
    ["500", 100],
  ])("'%s' da %s", (texto, esperado) => {
    expect(entero(texto, 1, 100)).toBe(esperado);
  });
});

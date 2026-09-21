# arrume

Generador y visualizador 3D de patrones de arrume (*pallet loading*).

Dadas las dimensiones del pallet y de la caja, calcula el mejor patron de
acomodo por nivel, apila los niveles pedidos y exporta un HTML interactivo.

## Instalacion

```bash
python -m venv .venv
.venv/Scripts/activate          # en Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

## Uso

```bash
python -m arrume                                   # configuracion por defecto
python -m arrume --pallet 120 100 --caja 40 30 25 --niveles 5
python -m arrume --sin-grafico                     # solo el informe
python -m arrume --caja 37.5 27.5 22 --altura-max 180 --peso-caja 12.5
python -m arrume --help                            # todas las opciones
```

Salida:

```
Pallet .............. 120 x 100 x 15 cm
Caja ................ 40 x 30 x 25 cm
Cajas por nivel ..... 10  (6 en posicion normal, 4 giradas)
Niveles ............. 5  (trabado)
Total de cajas ...... 50
Altura total ........ 140 cm
Aprovechamiento ..... 100.0 % de la superficie del pallet
```

## Como esta organizado

El nucleo no sabe que existe plotly; el dibujo es un adaptador del borde.

| Modulo | Responsabilidad |
| --- | --- |
| `arrume/domain/` | Modelos (`Pallet`, `Caja`, `Restricciones`, `Arrume`) y errores. Todo objeto construido es valido. |
| `arrume/packing/` | Estrategias de patron por nivel. `guillotina.py` es el motor actual. |
| `arrume/stacking.py` | Apila el patron nivel a nivel y arma el `Arrume`. |
| `arrume/reporting.py` | Calcula el informe y lo formatea. Devuelve datos y texto, no imprime. |
| `arrume/render/` | Unico lugar que importa plotly. |
| `arrume/cli.py` | Unica capa que imprime y que fija el codigo de salida. |

Para agregar un patron nuevo basta con una clase que cumpla el protocolo
`EstrategiaPatron` (`generar(area, caja) -> list[Pieza]`): el motor de
apilado no se toca.

## Tests

```bash
pytest
```

Los tests comprueban invariantes del acomodo (ninguna caja fuera del area,
ningun solapamiento, totales coherentes) contra todas las estrategias.

## Pendiente

- El trabado gira el nivel 180 grados; con un patron simetrico eso no cambia
  nada. Hace falta un patron alterno real (ver `tests/test_trabado.py`).
- Exportar con `include_plotlyjs="cdn"` para bajar el HTML de ~4.8 MB a ~50 KB.
- Aplicar `altura_max` / `peso_max` como restricciones duras, no solo avisos.

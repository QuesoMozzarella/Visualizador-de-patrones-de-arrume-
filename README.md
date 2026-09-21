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
python -m arrume --sin-trabado                     # apila en columna
python -m arrume --trabazon rotacion               # el trabado del proyecto original
python -m arrume --help                            # todas las opciones
```

Salida:

```
Pallet .............. 120 x 100 x 15 cm
Caja ................ 40 x 30 x 25 cm
Cajas por nivel ..... 10  (6 en posicion normal, 4 giradas)
Niveles ............. 5  (trabado)
Trabazon ............ 35 %  (mejor alterno, 0 de 10 cajas calcadas)
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
| `arrume/trabazon.py` | Mide la trabazon y decide el patron de los niveles impares. |
| `arrume/stacking.py` | Apila los patrones nivel a nivel y arma el `Arrume`. |
| `arrume/reporting.py` | Calcula el informe y lo formatea. Devuelve datos y texto, no imprime. |
| `arrume/render/` | Unico lugar que importa plotly. |
| `arrume/cli.py` | Unica capa que imprime y que fija el codigo de salida. |

Para agregar un patron nuevo basta con una clase que cumpla el protocolo
`EstrategiaPatron` (`generar(area, caja) -> list[Pieza]`): el motor de
apilado no se toca. Lo mismo con `Trabazon` (`alterno(...) -> list[Pieza]`)
para probar otra forma de alternar los niveles.

## Trabazon

Un arrume traba cuando las cajas de un nivel pisan las juntas del nivel de
abajo. Si cada caja se apoya sobre una sola caja, el arrume forma columnas
sueltas y se abre.

El informe lo mide: el porcentaje indica cuanto reparten su apoyo las cajas
de arriba (0 % = calcadas sobre las de abajo), y se acompana de cuantas
cajas quedaron calcadas.

`--trabazon mejor` (por defecto) prueba varios patrones alternos -- giro de
media vuelta, los dos espejos, arrimar el patron a cada esquina
aprovechando la holgura, y preferir la caja girada -- y se queda con el que
mas traba. `--trabazon rotacion` es el giro de 180 grados original, que solo
trababa en 3 de 10 configuraciones medidas; el modo `mejor` traba en 7.

Las 3 restantes son teselados perfectos: el nivel llena el pallet exacto y
no existe recolocacion posible. En ese caso el informe avisa en vez de
aparentar una trabazon que no hay; dejar vuelo suele desbloquearlas.

## Tests

```bash
pytest
```

Los tests comprueban invariantes del acomodo (ninguna caja fuera del area,
ningun solapamiento, totales coherentes) contra todas las estrategias.

## Pendiente

- Exportar con `include_plotlyjs="cdn"` para bajar el HTML de ~4.8 MB a ~50 KB.
- Aplicar `altura_max` / `peso_max` como restricciones duras, no solo avisos.

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

### La interfaz

Doble clic en `Arrume.bat`. Se abre el navegador con el formulario a un
lado y el arrume en 3D al otro, y se recalcula al cambiar cualquier medida.
Deja la ventana negra abierta mientras lo usas.

Sin doble clic:

```bash
arrume-gui                     # o: python -m arrume.web.servidor
arrume-gui --puerto 8080       # puerto fijo en vez de uno libre cualquiera
arrume-gui --no-abrir          # no abrir el navegador al arrancar
```

Escucha solo en `127.0.0.1` y no necesita internet: la libreria de dibujo
la sirve el propio programa desde el paquete instalado.

### La linea de comandos

Lo mismo sin interfaz, util para repetir o automatizar:

```bash
python -m arrume                                   # configuracion por defecto
python -m arrume --pallet 120 100 --caja 40 30 25 --niveles 5
python -m arrume --sin-grafico                     # solo el informe
python -m arrume --caja 37.5 27.5 22 --altura-max 180 --peso-caja 12.5
python -m arrume --sin-trabado                     # apila en columna
python -m arrume --trabazon rotacion               # el trabado del proyecto original
python -m arrume --html completo                   # HTML sin depender de internet
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
| `arrume/render/` | Unico lugar que importa plotly. `Renderer` arma la figura, `Exportador` la guarda. |
| `arrume/web/` | La interfaz: `servicio.py` traduce el formulario, `servidor.py` es el adaptador HTTP, `estaticos/` es la pagina. |
| `arrume/cli.py` | Unica capa que imprime y que fija el codigo de salida. |

Para agregar un patron nuevo basta con una clase que cumpla el protocolo
`EstrategiaPatron` (`generar(area, caja) -> list[Pieza]`): el motor de
apilado no se toca. Lo mismo con `Trabazon` (`alterno(...) -> list[Pieza]`)
para probar otra forma de alternar los niveles.

## La interfaz por dentro

La web es otro adaptador del borde, hermano de la CLI: el nucleo no sabe
que existe. Esta montada sobre la libreria estandar para no obligar a
instalar un framework, pero sin atar a ninguno.

- **Back:** las rutas son funciones puras `Peticion -> Respuesta` reunidas
  en `RUTAS`. Montarlas sobre Flask o FastAPI es mapear ese diccionario, y
  se prueban sin abrir ningun puerto.
- **Front:** la pagina es un archivo estatico cualquiera dentro de
  `estaticos/`. Sustituirla por el build de un React o un Vue es copiar su
  carpeta ahi; la API no cambia.

La API que consume la pagina, y que consumiria cualquier otra:

| Ruta | Que hace |
| --- | --- |
| `GET /` | la pagina |
| `GET /plotly.js` | la libreria de dibujo, desde el paquete local |
| `POST /api/arrume` | recibe el formulario, devuelve figura, cifras, avisos e informe |
| `GET /descargar` | el arrume como HTML autocontenido |

Un formulario invalido no es un error de HTTP: `POST /api/arrume` responde
200 con `{"ok": false, "error": "..."}` y la pagina lo muestra donde toca.

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

## El archivo HTML

Por defecto el HTML carga plotly desde su CDN: **56 KB** en vez de los
**4.8 MB** que ocupaba antes con la libreria incrustada, pero hace falta
internet para abrirlo. Con `--html completo` vuelve a quedar autocontenido.

## Tests

```bash
pytest
```

Los tests comprueban invariantes del acomodo (ninguna caja fuera del area,
ningun solapamiento, totales coherentes) contra todas las estrategias.

Las tres comprobaciones que corre la CI, y que conviene correr antes de
cada commit:

```bash
ruff check .    # estilo, imports y trampas comunes
mypy            # tipos del paquete arrume
pytest          # los 271 tests
```

## Pendiente

- La paleta de los niveles del 3D no pasa la validacion de color: dos
  niveles contiguos cuestan de distinguir incluso con vision normal. El
  detalle medido esta anotado sobre la constante `PALETA`, en
  `arrume/render/plotly3d.py`.
- Aplicar `altura_max` / `peso_max` como restricciones duras, no solo avisos.

"""
Generador de patrones de arrume (pallet loading) en 3D.

Dadas las dimensiones del pallet y de la caja, calcula automaticamente el
mejor patron de acomodo por nivel y apila los niveles que le pidas.

Uso:  python arrume.py
"""

import plotly.graph_objects as go

# =====================================================================
# 1. CONFIGURACION  -- edita solo esta seccion
# =====================================================================
PALLET_DX, PALLET_DY = 120, 100   # superficie del pallet (cm)
PALLET_DZ = 15                    # alto de la plataforma del pallet (cm)

CAJA_DX, CAJA_DY, CAJA_DZ = 40, 30, 25   # dimensiones de la caja (cm)

NIVELES = 5          # cuantos niveles (pisos) de cajas apilar
TRABADO = True       # True = cada nivel gira 180 grados (arrume trabado)
VUELO = 0            # cm que las cajas pueden sobresalir del pallet por lado
ALTURA_MAX = None    # ej. 180 -> avisa si el arrume total la supera
PESO_CAJA = None     # ej. 12.5 kg -> calcula el peso total del arrume

# =====================================================================
# 2. MOTOR DE EMPAQUETADO (corte guillotina con memoizacion)
# =====================================================================


def _cortes(limite, a, b):
    """Posiciones de corte utiles: todo i*a + j*b que quepa en 'limite'."""
    vals = set()
    i = 0
    while i * a <= limite:
        j = 0
        while i * a + j * b <= limite:
            vals.add(i * a + j * b)
            j += 1
        i += 1
    return sorted(v for v in vals if 0 < v < limite)


def _mejor(W, L, a, b, memo):
    """Mejor acomodo de cajas a*b dentro de un rectangulo W*L.

    Devuelve una lista de (x, y, dx, dy). Prueba bloques uniformes en las dos
    orientaciones y todos los cortes guillotina horizontales y verticales.
    """
    clave = (W, L)
    if clave in memo:
        return memo[clave]

    mejor = []

    # Opcion A: un bloque uniforme, en cada una de las dos orientaciones
    for dx, dy in ((a, b), (b, a)):
        nx, ny = W // dx, L // dy
        if nx and ny and nx * ny > len(mejor):
            mejor = [(ix * dx, iy * dy, dx, dy)
                     for ix in range(nx) for iy in range(ny)]

    # Opcion B: partir en dos por X y resolver cada mitad
    for x in _cortes(W, a, b):
        if 2 * x > W:
            break
        izq = _mejor(x, L, a, b, memo)
        der = _mejor(W - x, L, a, b, memo)
        if len(izq) + len(der) > len(mejor):
            mejor = izq + [(px + x, py, pdx, pdy) for px, py, pdx, pdy in der]

    # Opcion C: partir en dos por Y
    for y in _cortes(L, a, b):
        if 2 * y > L:
            break
        aba = _mejor(W, y, a, b, memo)
        arr = _mejor(W, L - y, a, b, memo)
        if len(aba) + len(arr) > len(mejor):
            mejor = aba + [(px, py + y, pdx, pdy) for px, py, pdx, pdy in arr]

    memo[clave] = mejor
    return mejor


def patron_nivel(area_dx, area_dy, caja_dx, caja_dy):
    """Calcula el patron de un nivel y lo centra sobre la superficie."""
    piezas = _mejor(area_dx, area_dy, caja_dx, caja_dy, {})
    if not piezas:
        return []
    usado_x = max(x + dx for x, y, dx, dy in piezas)
    usado_y = max(y + dy for x, y, dx, dy in piezas)
    ox = (area_dx - usado_x) / 2
    oy = (area_dy - usado_y) / 2
    return [(x + ox, y + oy, dx, dy) for x, y, dx, dy in piezas]


def construir_arrume():
    """Genera la lista completa de cajas: (x, y, z, dx, dy, dz, nivel)."""
    area_dx = PALLET_DX + 2 * VUELO
    area_dy = PALLET_DY + 2 * VUELO

    base = patron_nivel(area_dx, area_dy, CAJA_DX, CAJA_DY)
    if not base:
        raise SystemExit(
            "Ninguna caja de {}x{} cm cabe en un area de {}x{} cm. "
            "Revisa las dimensiones.".format(CAJA_DX, CAJA_DY, area_dx, area_dy)
        )

    cajas = []
    for nivel in range(NIVELES):
        z = PALLET_DZ + nivel * CAJA_DZ
        for x, y, dx, dy in base:
            if TRABADO and nivel % 2 == 1:
                # Giro de 180 grados del nivel completo -> trabazon
                x, y = area_dx - x - dx, area_dy - y - dy
            cajas.append((x - VUELO, y - VUELO, z, dx, dy, CAJA_DZ, nivel))
    return base, cajas


# =====================================================================
# 3. GEOMETRIA 3D
# =====================================================================

# Las 12 caras triangulares de una caja, con las normales hacia afuera
_CARAS = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
          (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
          (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]

_ARISTAS = [(0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)]


def _vertices(x, y, z, dx, dy, dz):
    return [(x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
            (x, y, z + dz), (x + dx, y, z + dz),
            (x + dx, y + dy, z + dz), (x, y + dy, z + dz)]


def malla(lista_cajas, color, nombre, etiquetas=None, opacidad=1.0):
    """Une varias cajas en un solo Mesh3d (mas rapido que uno por caja)."""
    vx, vy, vz, fi, fj, fk, texto = [], [], [], [], [], [], []
    for n, caja in enumerate(lista_cajas):
        base = 8 * n
        for px, py, pz in _vertices(*caja):
            vx.append(px)
            vy.append(py)
            vz.append(pz)
            texto.append(etiquetas[n] if etiquetas else nombre)
        for a, b, c in _CARAS:
            fi.append(base + a)
            fj.append(base + b)
            fk.append(base + c)
    return go.Mesh3d(x=vx, y=vy, z=vz, i=fi, j=fj, k=fk,
                     color=color, opacity=opacidad, flatshading=True,
                     name=nombre, text=texto, hoverinfo="text")


def aristas(lista_cajas, color="#1a1a1a", ancho=2):
    """Todas las aristas de todas las cajas en un solo trazo."""
    lx, ly, lz = [], [], []
    for caja in lista_cajas:
        v = _vertices(*caja)
        for a, b in _ARISTAS:
            lx += [v[a][0], v[b][0], None]
            ly += [v[a][1], v[b][1], None]
            lz += [v[a][2], v[b][2], None]
    return go.Scatter3d(x=lx, y=ly, z=lz, mode="lines",
                        line=dict(color=color, width=ancho),
                        hoverinfo="skip", showlegend=False)


def piezas_pallet():
    """Plataforma estilo europallet: tabla superior, tacos y tabla inferior."""
    t = max(2, PALLET_DZ * 0.15)          # espesor de las tablas
    h = PALLET_DZ - 2 * t                 # alto de los tacos
    piezas = [(0, 0, PALLET_DZ - t, PALLET_DX, PALLET_DY, t),
              (0, 0, 0, PALLET_DX, PALLET_DY, t)]
    ancho_taco = PALLET_DX * 0.12
    for f in (0.0, 0.5, 1.0):             # tres tacos a lo largo de X
        piezas.append((f * (PALLET_DX - ancho_taco), 0, t,
                       ancho_taco, PALLET_DY, h))
    return piezas


# =====================================================================
# 4. INFORME Y DIBUJO
# =====================================================================

PALETA = ["#7fb3d5", "#a9dfbf", "#f9e79f", "#f5b7b1", "#d7bde2", "#a3e4d7"]


def informe(base, cajas):
    por_nivel = len(base)
    total = len(cajas)
    alto = PALLET_DZ + NIVELES * CAJA_DZ
    aprov = 100 * por_nivel * CAJA_DX * CAJA_DY / (PALLET_DX * PALLET_DY)
    normales = sum(1 for x, y, dx, dy in base if (dx, dy) == (CAJA_DX, CAJA_DY))

    print("Pallet .............. {} x {} x {} cm".format(
        PALLET_DX, PALLET_DY, PALLET_DZ))
    print("Caja ................ {} x {} x {} cm".format(
        CAJA_DX, CAJA_DY, CAJA_DZ))
    print("Cajas por nivel ..... {}  ({} en posicion normal, {} giradas)".format(
        por_nivel, normales, por_nivel - normales))
    print("Niveles ............. {}  ({})".format(
        NIVELES, "trabado" if TRABADO else "en columna"))
    print("Total de cajas ...... {}".format(total))
    print("Altura total ........ {} cm".format(alto))
    print("Aprovechamiento ..... {:.1f} % de la superficie del pallet".format(aprov))
    if PESO_CAJA:
        print("Peso total .......... {:.1f} kg".format(total * PESO_CAJA))
    if ALTURA_MAX and alto > ALTURA_MAX:
        print("  AVISO: supera la altura maxima de {} cm por {} cm.".format(
            ALTURA_MAX, alto - ALTURA_MAX))


def dibujar(cajas):
    fig = go.Figure()

    pal = piezas_pallet()
    fig.add_trace(malla(pal, "#9a7b4f", "Pallet"))
    fig.add_trace(aristas(pal, "#4a3a25", 1.5))

    # Un Mesh3d por nivel, coloreado para que se vea la trabazon
    for nivel in range(NIVELES):
        delnivel = [c for c in cajas if c[6] == nivel]
        cuerpos = [c[:6] for c in delnivel]
        etiquetas = ["Nivel {} - caja {}".format(nivel + 1, n + 1)
                     for n in range(len(delnivel))]
        fig.add_trace(malla(cuerpos, PALETA[nivel % len(PALETA)],
                            "Nivel {}".format(nivel + 1), etiquetas))

    fig.add_trace(aristas([c[:6] for c in cajas]))

    alto = PALLET_DZ + NIVELES * CAJA_DZ
    fig.update_layout(
        title="Arrume: {} cajas = {} por nivel x {} niveles - {} cm de alto".format(
            len(cajas), len(cajas) // NIVELES, NIVELES, alto),
        scene=dict(xaxis_title="Ancho (X) cm",
                   yaxis_title="Profundidad (Y) cm",
                   zaxis_title="Alto (Z) cm",
                   aspectmode="data",
                   camera=dict(eye=dict(x=1.6, y=-1.6, z=1.1))),
        showlegend=False,
        margin=dict(l=0, r=0, t=50, b=0),
    )
    return fig


if __name__ == "__main__":
    base, cajas = construir_arrume()
    informe(base, cajas)
    dibujar(cajas).write_html("arrume.html", auto_open=True)
    print("\nGrafico guardado en arrume.html")

"""Adaptador de dibujo: convierte un Arrume en una figura 3D de Plotly.

Este es el unico modulo del proyecto que importa plotly. Si manana hay que
exportar a otro formato, se agrega otro adaptador y el dominio no se toca.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import plotly.graph_objects as go

from ..domain.models import Arrume, Numero, Pallet

# Las 12 caras triangulares de una caja, con las normales hacia afuera
_CARAS = [
    (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
    (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
    (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
]

_ARISTAS = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
]

PALETA = ["#7fb3d5", "#a9dfbf", "#f9e79f", "#f5b7b1", "#d7bde2", "#a3e4d7"]

_Cuerpo = Sequence[Numero]  # (x, y, z, dx, dy, dz)


def _vertices(x, y, z, dx, dy, dz):
    return [
        (x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
        (x, y, z + dz), (x + dx, y, z + dz),
        (x + dx, y + dy, z + dz), (x, y + dy, z + dz),
    ]


def malla(
    cuerpos: Sequence[_Cuerpo],
    color: str,
    nombre: str,
    etiquetas: Optional[Sequence[str]] = None,
    opacidad: float = 1.0,
) -> go.Mesh3d:
    """Une varias cajas en un solo Mesh3d (mas rapido que uno por caja)."""
    vx, vy, vz, fi, fj, fk, texto = [], [], [], [], [], [], []
    for n, cuerpo in enumerate(cuerpos):
        base = 8 * n
        for px, py, pz in _vertices(*cuerpo):
            vx.append(px)
            vy.append(py)
            vz.append(pz)
            texto.append(etiquetas[n] if etiquetas else nombre)
        for a, b, c in _CARAS:
            fi.append(base + a)
            fj.append(base + b)
            fk.append(base + c)
    return go.Mesh3d(
        x=vx, y=vy, z=vz, i=fi, j=fj, k=fk,
        color=color, opacity=opacidad, flatshading=True,
        name=nombre, text=texto, hoverinfo="text",
    )


def aristas(
    cuerpos: Sequence[_Cuerpo], color: str = "#1a1a1a", ancho: float = 2
) -> go.Scatter3d:
    """Todas las aristas de todas las cajas en un solo trazo."""
    lx, ly, lz = [], [], []
    for cuerpo in cuerpos:
        v = _vertices(*cuerpo)
        for a, b in _ARISTAS:
            lx += [v[a][0], v[b][0], None]
            ly += [v[a][1], v[b][1], None]
            lz += [v[a][2], v[b][2], None]
    return go.Scatter3d(
        x=lx, y=ly, z=lz, mode="lines",
        line=dict(color=color, width=ancho),
        hoverinfo="skip", showlegend=False,
    )


def piezas_pallet(pallet: Pallet) -> List[tuple]:
    """Plataforma estilo europallet: tabla superior, tacos y tabla inferior."""
    t = max(2, pallet.alto * 0.15)     # espesor de las tablas
    h = pallet.alto - 2 * t            # alto de los tacos
    piezas = [
        (0, 0, pallet.alto - t, pallet.ancho, pallet.profundidad, t),
        (0, 0, 0, pallet.ancho, pallet.profundidad, t),
    ]
    if h > 0:
        ancho_taco = pallet.ancho * 0.12
        for f in (0.0, 0.5, 1.0):      # tres tacos a lo largo de X
            piezas.append(
                (f * (pallet.ancho - ancho_taco), 0, t, ancho_taco, pallet.profundidad, h)
            )
    return piezas


def construir_figura(
    arrume: Arrume, paleta: Optional[Sequence[str]] = None
) -> go.Figure:
    """Arma la figura 3D completa: pallet, niveles de cajas y aristas."""
    colores = list(paleta) if paleta else PALETA
    fig = go.Figure()

    plataforma = piezas_pallet(arrume.pallet)
    fig.add_trace(malla(plataforma, "#9a7b4f", "Pallet"))
    fig.add_trace(aristas(plataforma, "#4a3a25", 1.5))

    # Un Mesh3d por nivel, coloreado para que se vea la trabazon
    for nivel in range(arrume.niveles):
        del_nivel = [c for c in arrume.cajas if c.nivel == nivel]
        etiquetas = [
            "Nivel {} - caja {}".format(nivel + 1, n + 1)
            for n in range(len(del_nivel))
        ]
        fig.add_trace(
            malla(
                [c.cuerpo for c in del_nivel],
                colores[nivel % len(colores)],
                "Nivel {}".format(nivel + 1),
                etiquetas,
            )
        )

    fig.add_trace(aristas([c.cuerpo for c in arrume.cajas]))

    fig.update_layout(
        title="Arrume: {} cajas = {} por nivel x {} niveles - {} cm de alto".format(
            arrume.total_cajas,
            arrume.cajas_por_nivel,
            arrume.niveles,
            arrume.altura_total,
        ),
        scene=dict(
            xaxis_title="Ancho (X) cm",
            yaxis_title="Profundidad (Y) cm",
            zaxis_title="Alto (Z) cm",
            aspectmode="data",
            camera=dict(eye=dict(x=1.6, y=-1.6, z=1.1)),
        ),
        showlegend=False,
        margin=dict(l=0, r=0, t=50, b=0),
    )
    return fig


class Plotly3D:
    """Renderer: arma la figura 3D del arrume."""

    nombre = "plotly 3d"

    def __init__(self, paleta: Optional[Sequence[str]] = None) -> None:
        self.paleta = list(paleta) if paleta else PALETA

    def render(self, arrume: Arrume) -> go.Figure:
        return construir_figura(arrume, self.paleta)


class ExportadorHTML:
    """Exportador: escribe la figura como pagina HTML.

    'cdn' deja la libreria fuera del archivo (~50 KB, necesita internet
    para abrirlo); 'completo' la incrusta (~4.8 MB, se abre sin conexion).
    """

    extension = ".html"

    MODOS = {"cdn": "cdn", "completo": True}

    def __init__(self, modo: str = "cdn") -> None:
        if modo not in self.MODOS:
            raise ValueError(
                "Modo de HTML desconocido: {}. Use {}.".format(
                    modo, " o ".join(sorted(self.MODOS))
                )
            )
        self.modo = modo

    def exportar(self, figura: go.Figure, ruta: str, abrir: bool = False) -> str:
        figura.write_html(
            ruta, include_plotlyjs=self.MODOS[self.modo], auto_open=abrir
        )
        return ruta

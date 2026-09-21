import plotly.graph_objects as go
import numpy as np

# 1. Definir la función que crea una caja 3D
def create_box(x, y, z, dx, dy, dz, color, name):
    """
    Crea los vértices y caras para dibujar una caja 3D en Plotly.
    x, y, z: Coordenadas de la esquina inferior trasera izquierda.
    dx, dy, dz: Dimensiones de la caja (ancho, profundo, alto).
    """
    # 8 Vértices de la caja
    x_coords = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
    y_coords = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
    z_coords = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]
    
    # Índices de los triángulos que forman las 6 caras de la caja
    i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
    j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
    k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]

    return go.Mesh3d(
        x=x_coords, y=y_coords, z=z_coords,
        i=i, j=j, k=k,
        color=color,
        opacity=0.8, # Un poco de transparencia para ver los bordes
        name=name,
        hoverinfo="name"
    )

# 2. Datos del Pallet (Ejemplo: Europallet estándar)
pallet_dx, pallet_dy, pallet_dz = 120, 80, 15  # Ancho, profundo, alto de la base (cm)

# 3. Datos de las cajas acomodadas (Estos datos te los daría py3dbp)
# Formato: [x, y, z, ancho(dx), profundo(dy), alto(dz), color, nombre]
cajas = [
    # Primera capa (Base)
    [0, 0, 15, 40, 40, 30, 'lightblue', 'Caja 1'],
    [40, 0, 15, 40, 40, 30, 'lightblue', 'Caja 2'],
    [80, 0, 15, 40, 40, 30, 'lightblue', 'Caja 3'],
    [0, 40, 15, 40, 40, 30, 'lightblue', 'Caja 4'],
    [40, 40, 15, 40, 40, 30, 'lightblue', 'Caja 5'],
    [80, 40, 15, 40, 40, 30, 'lightblue', 'Caja 6'],
    # Segunda capa
    [0, 0, 45, 60, 40, 30, 'lightgreen', 'Caja 7 - Grande'],
    [60, 0, 45, 60, 40, 30, 'lightgreen', 'Caja 8 - Grande'],
]

# 4. Construir la figura
fig = go.Figure()

# Agregar la base del pallet (dibujado como una caja gris plana)
fig.add_trace(create_box(0, 0, 0, pallet_dx, pallet_dy, pallet_dz, 'gray', 'Pallet (Base)'))

# Agregar cada una de las cajas iterando sobre nuestra lista
for caja in cajas:
    fig.add_trace(create_box(caja[0], caja[1], caja[2], 
                             caja[3], caja[4], caja[5], 
                             caja[6], caja[7]))

# 5. Configurar el diseño (Ejes y proporciones correctas)
fig.update_layout(
    title='Visualización de Patrón de Arrume (Pallet Loading)',
    scene=dict(
        xaxis_title='Ancho (X) cm',
        yaxis_title='Profundidad (Y) cm',
        zaxis_title='Alto (Z) cm',
        # Para que los centímetros sean proporcionales en el gráfico (sin distorsión)
        aspectmode='data' 
    ),
    showlegend=False
)

# 6. Mostrar el gráfico interactivo
# Escribimos un HTML real y lo abrimos: es mucho más fiable que fig.show(),
# que depende de un servidor local de un solo uso.
fig.write_html("pallet.html", auto_open=True)
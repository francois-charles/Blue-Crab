import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle, Circle
import time

# Configuration de la page
st.set_page_config(page_title="Simulation Dispersion Canet", layout="wide")

# --- STYLE ET COULEURS ---
BLEU_MER = '#003554'
VERT_TERRE = '#1b4332'
# OR_RECRUT = '#ffbc42'
OR_RECRUT='blue'
CYAN_LARGE = '#00f5d4'
SABLE = '#e9c46a'

# --- MARQUEUR CRABE ---
def get_crab_marker():
    # Dessin d'un crabe simplifié (corps + pinces)
    verts = [
        (-1, -0.5), (1, -0.5), (1, 0.5), (-1, 0.5), (-1, -0.5), # Corps
        (-1.2, 0.6), (-0.8, 1.2), (-0.4, 0.6), # Pince G
        (1.2, 0.6), (0.8, 1.2), (0.4, 0.6),   # Pince D
    ]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY,
             Path.MOVETO, Path.LINETO, Path.LINETO, Path.MOVETO, Path.LINETO, Path.LINETO]
    return Path(verts, codes)

crab_marker = get_crab_marker()

# --- PARAMÈTRES ---
st.sidebar.header("🕹️ Configuration")
wind_dir = st.sidebar.slider("Origine du Vent (°)", 0, 359, 90, help="D'où vient le vent (0°=N, 90°=E...)")
wind_power = st.sidebar.slider("Vitesse du Vent (m/s)", 0, 25, 12)
nb_larves = st.sidebar.select_slider("Nombre de Propagules", options=[5, 250, 500, 750, 1000])
tide_power = st.sidebar.slider("Force de la Marée", 0.0, 1.5, 0.5)
start_btn = st.sidebar.button("🚀 Lancer l'Animation")

# --- GÉOMÉTRIE ---
def get_organic_path(points):
    return Path(points, [Path.MOVETO] + [Path.CURVE4] * (len(points) - 1))

nodes_lagune = [
    (15, 30), (12, 45), (15, 70), (30, 85), (45, 75), 
    (51.5, 59), (51.5, 41), (42, 30), (25, 15), (15, 30)
]
path_lagune = get_organic_path(nodes_lagune)

# --- INITIALISATION ---
if 'x' not in st.session_state or start_btn:
    st.session_state.x = np.random.normal(60, 4, nb_larves)
    st.session_state.y = np.random.normal(50, 16, nb_larves)
    st.session_state.status = np.zeros(nb_larves)
    st.session_state.depth = np.zeros(nb_larves)

# --- ROSE DES VENTS ---
def draw_wind_rose(ax, center_x, center_y, wind_dir, wind_power):
    radius = 12
    ax.add_patch(Circle((center_x, center_y), radius, color='white', alpha=0.1, zorder=10))
    
    for label, angle in [('N', 0), ('NO', 315),('E', 90),('SE',135), ('S', 180), ('O', 270)]:
        rad = np.radians(angle)
        lx = center_x + radius * 1.5 * np.sin(rad)
        ly = center_y + radius * 1.5 * np.cos(rad)
        ax.text(lx, ly, label, color='white', ha='center', va='center', weight='bold')

    flow_dir_rad = np.radians(wind_dir + 180)
    arrow_scale = max(0.3, wind_power / 16.5)
    arrow_len = radius * 0.9 * arrow_scale
    dx = arrow_len * np.sin(flow_dir_rad)
    dy = arrow_len * np.cos(flow_dir_rad)
    
    ax.arrow(center_x, center_y, dx, dy, head_width=3, head_length=4, 
             fc=CYAN_LARGE, ec='white', linewidth=2, length_includes_head=True, zorder=15)
    ax.add_patch(Circle((center_x, center_y), 0.8, color='white', zorder=16))

# --- RENDU ---
def draw_map(x, y, status, step, wind_dir, wind_power):
    fig, ax = plt.subplots(figsize=(11, 7), facecolor=CYAN_LARGE)
    ax.set_facecolor(BLEU_MER)
    
    coast = [(0,-10), (48.5,-10), (48.5,41), (35,50), (48.5,59), (48.5,110), (0,110)]
    ax.fill([p[0] for p in coast], [p[1] for p in coast], color=VERT_TERRE, zorder=1)
    ax.add_patch(PathPatch(path_lagune, facecolor=CYAN_LARGE, edgecolor=CYAN_LARGE, lw=1, zorder=2))
    ax.add_patch(Rectangle((48.5, -10), 3, 51, color=SABLE, zorder=3))
    ax.add_patch(Rectangle((48.5, 60), 3, 55, color=SABLE, zorder=3))

    # Particules - Larves (Status 0)
    ax.scatter(x[status==0], y[status==0], s=12, c='white', alpha=0.6, zorder=5)
    
    # Particules - PETITS CRABES (Status 1)
    ax.scatter(x[status==1], y[status==1], s=60,lw=0.2, marker=crab_marker, c=OR_RECRUT, edgecolors='white', zorder=6)
    
    # Échouages (Status 2)
    ax.scatter(x[status==2], y[status==2], s=15, c='#ef233c', marker='x', alpha=0.4, zorder=4)

    draw_wind_rose(ax, 115, 85, wind_dir, wind_power)
    ax.set_xlim(-5, 140)
    ax.set_ylim(-10, 110)
    ax.axis('off')
    ax.set_title(f"Simulation : Vent du {wind_dir}° ({wind_power} m/s)", color='white', loc='left', pad=-20)
    return fig

# --- BOUCLE ---
placeholder = st.empty()

if start_btn:
    rad_flux = np.radians(wind_dir + 180)
    dx_wind = np.sin(rad_flux) * (wind_power / 10.0)
    dy_wind = np.cos(rad_flux) * (wind_power / 10.0)
    diff = 0.1 + (wind_power * 0.02)

    for step in range(50):
        # COMPOSANTE DE MARÉE : Oscillation vers la côte (dx négatif)
        # La marée ramène vers le littoral (X=48.5) surtout quand on est proche
        tide_x = -abs(np.sin(step * 0.3)) * tide_power 
        
        for i in range(nb_larves):
            if st.session_state.status[i] == 0:
                # On ajoute la marée (tide_x) au déplacement du vent
                st.session_state.x[i] += dx_wind + tide_x + np.random.normal(0, diff)
                st.session_state.y[i] += dy_wind + np.random.normal(0, diff)
                
                cx, cy = st.session_state.x[i], st.session_state.y[i]
                
                if path_lagune.contains_point((cx, cy)):
                    st.session_state.depth[i] += 1
                    if st.session_state.depth[i] >= 5: st.session_state.status[i] = 1
                elif 48.5 <= cx <= 51.5 and (cy < 41 or cy > 59):
                    st.session_state.status[i] = 2
                elif cx < 48.5:
                    st.session_state.status[i] = 2
                elif cx > 140 or cy > 110 or cy < -10:
                    st.session_state.status[i] = 3

        with placeholder.container():
            fig = draw_map(st.session_state.x, st.session_state.y, st.session_state.status, step, wind_dir, wind_power)
            st.pyplot(fig)
            plt.close(fig)
        time.sleep(0.02)

    recrutement = int(np.sum(st.session_state.status == 1))
    st.success(f"Recrutement final : {recrutement} crabes installés dans la lagune.")
else:
    fig = draw_map(st.session_state.x, st.session_state.y, st.session_state.status, 0, wind_dir, wind_power)
    placeholder.pyplot(fig)


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation Dispersion Canet - Optimisée pour Android
Created on Wed Dec 31 16:18:35 2025
@author: charles
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle, Circle
import time

# Configuration responsive
st.set_page_config(
    page_title="Dispersion Canet",
    layout="wide",
    initial_sidebar_state="collapsed"  # Masqué par défaut sur mobile
)

# --- STYLE ---
BLEU_MER = '#003554'
VERT_TERRE = '#1b4332'
OR_RECRUT = 'blue'
CYAN_LARGE = '#003554'
SABLE = '#e9c46a'

# --- CSS MOBILE ---
st.markdown("""
<style>
    /* Réduction des marges sur mobile */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* Sidebar plus compacte */
    section[data-testid="stSidebar"] {
        width: 280px !important;
    }
    /* Boutons plus tactiles */
    .stButton button {
        height: 3rem;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- MARQUEUR CRABE OPTIMISÉ ---
def get_crab_marker():
    verts = []
    codes = []
    
    # Corps simplifié (moins de points = plus rapide)
    verts += [(-1, -0.7), (1, -0.7), (1.3, 0), (1, 0.7), (-1, 0.7), (-1.3, 0), (-1, -0.7)]
    codes += [Path.MOVETO] + [Path.LINETO]*5 + [Path.CLOSEPOLY]
    
    # Pinces
    for side in [-1, 1]:
        verts += [(side * 0.7, 0.4), (side * 1.4, 1.2), (side * 0.4, 1.2), (side * 0.7, 0.4)]
        codes += [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    
    # Pattes réduites (4 au lieu de 8 pour performances)
    for side in [-1, 1]:
        for angle_offset in [-0.4, 0, 0.4]:
            verts += [(side * 0.8, angle_offset), (side * 2.5, angle_offset + 0.3), (side * 3.5, angle_offset - 0.3)]
            codes += [Path.MOVETO, Path.LINETO, Path.LINETO]
    
    return Path(verts, codes)

crab_marker = get_crab_marker()

# --- PARAMÈTRES COMPACTS ---
with st.sidebar:
    st.header("⚙️ Configuration")
    wind_dir = st.slider("🧭 Origine Vent (°)", 0, 359, 90, 
                         help="0°=Nord, 90°=Est, 180°=Sud, 270°=Ouest")
    wind_power = st.slider("💨 Vitesse (m/s)", 0, 20, 12)
    nb_larves = st.slider("🦀 Propagules", 0, 1000, 500, step=50)
    tide_power = st.slider("🌊 Marée", 0.0, 1.5, 0.5, step=0.1)
    start_btn = st.button("🚀 LANCER", use_container_width=True)

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
    st.session_state.x = np.random.normal(70, 4, nb_larves)
    st.session_state.y = np.random.normal(50, 16, nb_larves)
    st.session_state.status = np.zeros(nb_larves)
    st.session_state.depth = np.zeros(nb_larves)

# --- ROSE DES VENTS SIMPLIFIÉE ---
def draw_wind_rose(ax, center_x, center_y, wind_dir, wind_power):
    radius = 12
    
    # Fond discret
    ax.add_patch(Circle((center_x, center_y), radius, color='white', alpha=0.05, zorder=10))
    
    # Directions principales uniquement (8 directions)
    directions = [('N', 0), ('NE', 45), ('E', 90), ('SE', 135), 
                  ('S', 180), ('SO', 225), ('O', 270), ('NO', 315)]
    
    for label, angle in directions:
        rad = np.radians(angle)
        
        # Segments fins
        x_start = center_x + 0.8 * np.sin(rad)
        y_start = center_y + 0.8 * np.cos(rad)
        x_end = center_x + radius * np.sin(rad)
        y_end = center_y + radius * np.cos(rad)
        ax.plot([x_start, x_end], [y_start, y_end], 
                color='white', linewidth=1.2, alpha=0.5, zorder=11)
        
        # Labels
        lx = center_x + radius * 1.4 * np.sin(rad)
        ly = center_y + radius * 1.4 * np.cos(rad)
        ax.text(lx, ly, label, color='white', ha='center', va='center', 
                fontsize=7, weight='bold', zorder=12)
    
    # Flèche du vent
    flow_dir_rad = np.radians(wind_dir + 180)
    arrow_scale = max(0.3, wind_power / 16.5)
    arrow_len = radius * 1.1 * arrow_scale
    
    dx = arrow_len * np.sin(flow_dir_rad)
    dy = arrow_len * np.cos(flow_dir_rad)
    
    ax.arrow(center_x, center_y, dx, dy, head_width=2.5, head_length=3.5, 
             fc='white', ec='white', linewidth=1.5, 
             length_includes_head=True, zorder=15)
    
    ax.add_patch(Circle((center_x, center_y), 0.6, color='white', zorder=16))

# --- RENDU OPTIMISÉ MOBILE ---
def draw_map(x, y, status, step, wind_dir, wind_power):
    # DPI réduit pour mobile (120 au lieu de 300)
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=CYAN_LARGE, dpi=120)
    ax.set_facecolor(BLEU_MER)
    
    # Géométrie
    coast = [(0,-10), (48.5,-10), (48.5,41), (35,50), (48.5,59), (48.5,110), (0,110)]
    ax.fill([p[0] for p in coast], [p[1] for p in coast], color=VERT_TERRE, zorder=1)
    ax.add_patch(PathPatch(path_lagune, facecolor=CYAN_LARGE, edgecolor=CYAN_LARGE, lw=1, zorder=2))
    ax.add_patch(Rectangle((48.5, -10), 3, 51, color=SABLE, zorder=3))
    ax.add_patch(Rectangle((48.5, 60), 3, 55, color=SABLE, zorder=3))
    
    # Particules (tailles réduites pour mobile)
    ax.scatter(x[status==0], y[status==0], s=8, c='white', alpha=0.6, zorder=5)
    
    # Crabes (taille adaptée)
    if np.sum(status==1) > 0:
        ax.scatter(x[status==1], y[status==1], 
                   s=180, lw=0.4, marker=crab_marker, 
                   c='blue', edgecolors='white', alpha=0.8, zorder=6)
    
    # Échouages
    ax.scatter(x[status==2], y[status==2], s=12, c='#ef233c', marker='x', alpha=0.4, zorder=4)
    
    # Rose des vents
    draw_wind_rose(ax, 115, 85, wind_dir, wind_power)
    
    ax.set_xlim(-5, 140)
    ax.set_ylim(-10, 110)
    ax.axis('off')
    
    # Titre compact
    ax.text(2, 105, f"Vent {wind_dir}° • {wind_power} m/s", 
            color='white', fontsize=10, weight='bold', va='top')
    
    return fig

# --- BOUCLE D'ANIMATION ---
placeholder = st.empty()

if start_btn:
    rad_flux = np.radians(wind_dir + 180)
    dx_wind = np.sin(rad_flux) * (wind_power / 10.0)
    dy_wind = np.cos(rad_flux) * (wind_power / 10.0)
    diff = 0.1 + (wind_power * 0.02)
    
    # Barre de progression mobile
    progress_bar = st.progress(0)
    
    for step in range(50):
        # Mise à jour progression
        progress_bar.progress((step + 1) / 50)
        
        # Marée
        tide_x = -abs(np.sin(step * 0.3)) * tide_power 
        
        for i in range(nb_larves):
            if st.session_state.status[i] == 0:
                st.session_state.x[i] += dx_wind + tide_x + np.random.normal(0, diff)
                st.session_state.y[i] += dy_wind + np.random.normal(0, diff)
                
                cx, cy = st.session_state.x[i], st.session_state.y[i]
                
                if path_lagune.contains_point((cx, cy)):
                    st.session_state.depth[i] += 1
                    if st.session_state.depth[i] >= 12: 
                        st.session_state.status[i] = 1
                elif 48.5 <= cx <= 51.5 and (cy < 41 or cy > 59):
                    st.session_state.status[i] = 2
                elif cx < 48.5:
                    st.session_state.status[i] = 2
                elif cx > 140 or cy > 110 or cy < -10:
                    st.session_state.status[i] = 3
            elif st.session_state.status[i] == 1:
                st.session_state.x[i] += np.random.normal(0, 0.7) 
                st.session_state.y[i] += np.random.normal(0, 1)
        
        # Mise à jour visuelle toutes les 2 frames pour fluidité
        if step % 2 == 0:
            with placeholder.container():
                fig = draw_map(st.session_state.x, st.session_state.y, 
                               st.session_state.status, step, wind_dir, wind_power)
                st.pyplot(fig)
                plt.close(fig)
        
        time.sleep(0.03)  # Légèrement plus lent pour stabilité mobile
    
    progress_bar.empty()
    
    recrutement = int(np.sum(st.session_state.status == 1))
    echoues = int(np.sum(st.session_state.status == 2))
    
    # Affichage des résultats en colonnes pour mobile
    col1, col2, col3 = st.columns(3)
    col1.metric("🦀 Recrutés", recrutement)
    col2.metric("❌ Échoués", echoues)
    col3.metric("📊 Taux", f"{recrutement/nb_larves*100:.1f}%")

else:
    fig = draw_map(st.session_state.x, st.session_state.y, 
                   st.session_state.status, 0, wind_dir, wind_power)
    placeholder.pyplot(fig)

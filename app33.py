#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation Dispersion Canet - Version Ultra Légère Mobile
@author: charles
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle, Circle
import time

st.set_page_config(page_title="Dispersion Canet", layout="wide", initial_sidebar_state="collapsed")

# --- STYLE ---
BLEU_MER = '#003554'
VERT_TERRE = '#1b4332'
SABLE = '#e9c46a'

# --- PARAMÈTRES ULTRA COMPACTS ---
with st.sidebar:
    st.header("⚙️ Config")
    wind_dir = st.slider("🧭 Vent (°)", 0, 359, 90, step=15)
    wind_power = st.slider("💨 Vitesse", 0, 20, 12, step=2)
    nb_larves = st.slider("🦀 Nombre", 100, 1000, 300, step=100)
    tide_power = st.slider("🌊 Marée", 0.0, 1.5, 0.5, step=0.25)
    start_btn = st.button("🚀 START", use_container_width=True)

# --- GÉOMÉTRIE SIMPLIFIÉE ---
def get_organic_path(points):
    return Path(points, [Path.MOVETO] + [Path.LINETO] * (len(points) - 1))  # LINETO au lieu de CURVE4 !

nodes_lagune = [
    (15, 30), (12, 45), (15, 70), (30, 85), (45, 75), 
    (51.5, 59), (51.5, 41), (42, 30), (25, 15), (15, 30)
]
path_lagune = get_organic_path(nodes_lagune)

# --- INITIALISATION ---
if 'x' not in st.session_state or start_btn:
    st.session_state.x = np.random.normal(70, 4, nb_larves)
    st.session_state.y = np.random.normal(50, 16, nb_larves)
    st.session_state.status = np.zeros(nb_larves, dtype=np.int8)  # int8 pour économie mémoire
    st.session_state.depth = np.zeros(nb_larves, dtype=np.int8)

# --- ROSE DES VENTS MINIMALISTE ---
def draw_wind_rose(ax, cx, cy, wind_dir, wind_power):
    r = 10
    
    # Seulement 4 directions cardinales
    for label, angle in [('N', 0), ('E', 90), ('S', 180), ('O', 270)]:
        rad = np.radians(angle)
        lx = cx + r * 1.3 * np.sin(rad)
        ly = cy + r * 1.3 * np.cos(rad)
        ax.text(lx, ly, label, color='white', ha='center', va='center', 
                fontsize=9, weight='bold')
    
    # Flèche simple
    flow_rad = np.radians(wind_dir + 180)
    arrow_len = r * 0.8
    dx = arrow_len * np.sin(flow_rad)
    dy = arrow_len * np.cos(flow_rad)
    
    ax.arrow(cx, cy, dx, dy, head_width=2, head_length=2, 
             fc='white', ec='white', linewidth=2, zorder=15)
    ax.add_patch(Circle((cx, cy), 0.5, color='white', zorder=16))

# --- RENDU ULTRA LÉGER ---
def draw_map(x, y, status, step, wind_dir, wind_power):
    # DPI minimal + figure petite
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=BLEU_MER, dpi=72)
    ax.set_facecolor(BLEU_MER)
    
    # Géométrie simplifiée (pas de courbes)
    coast = [(0,-10), (48.5,-10), (48.5,41), (35,50), (48.5,59), (48.5,110), (0,110)]
    ax.fill([p[0] for p in coast], [p[1] for p in coast], color=VERT_TERRE, zorder=1)
    ax.add_patch(PathPatch(path_lagune, facecolor=BLEU_MER, edgecolor=BLEU_MER, lw=1, zorder=2))
    ax.add_patch(Rectangle((48.5, -10), 3, 51, color=SABLE, zorder=3))
    ax.add_patch(Rectangle((48.5, 60), 3, 55, color=SABLE, zorder=3))
    
    # Particules ultra simples (pas de crabes détaillés !)
    ax.scatter(x[status==0], y[status==0], s=6, c='white', alpha=0.5, zorder=5)
    ax.scatter(x[status==1], y[status==1], s=40, c='blue', marker='*', 
               edgecolors='white', lw=0.5, alpha=0.7, zorder=6)
    ax.scatter(x[status==2], y[status==2], s=8, c='red', marker='x', alpha=0.3, zorder=4)
    
    # Rose minimaliste
    draw_wind_rose(ax, 115, 85, wind_dir, wind_power)
    
    ax.set_xlim(-5, 140)
    ax.set_ylim(-10, 110)
    ax.axis('off')
    ax.text(2, 105, f"Étape {step}/30 • {wind_power}m/s", 
            color='white', fontsize=9, weight='bold')
    
    plt.tight_layout(pad=0)
    return fig

# --- ANIMATION ULTRA OPTIMISÉE ---
placeholder = st.empty()

if start_btn:
    rad_flux = np.radians(wind_dir + 180)
    dx_wind = np.sin(rad_flux) * (wind_power / 10.0)
    dy_wind = np.cos(rad_flux) * (wind_power / 10.0)
    diff = 0.1 + (wind_power * 0.02)
    
    progress = st.progress(0)
    
    # RÉDUCTION À 30 ÉTAPES
    for step in range(30):
        progress.progress((step + 1) / 30)
        
        tide_x = -abs(np.sin(step * 0.3)) * tide_power
        
        # Calcul vectorisé (plus rapide que boucle)
        mobile = st.session_state.status == 0
        
        # Mise à jour positions (vectorisé)
        st.session_state.x[mobile] += dx_wind + tide_x + np.random.normal(0, diff, mobile.sum())
        st.session_state.y[mobile] += dy_wind + np.random.normal(0, diff, mobile.sum())
        
        # Collision (boucle simplifiée)
        for i in np.where(mobile)[0]:
            cx, cy = st.session_state.x[i], st.session_state.y[i]
            
            if path_lagune.contains_point((cx, cy)):
                st.session_state.depth[i] += 1
                if st.session_state.depth[i] >= 8:  # Réduit de 12 à 8
                    st.session_state.status[i] = 1
            elif 48.5 <= cx <= 51.5 and (cy < 41 or cy > 59):
                st.session_state.status[i] = 2
            elif cx < 48.5 or cx > 140 or cy > 110 or cy < -10:
                st.session_state.status[i] = 2
        
        # Crabes bougent
        recruits = st.session_state.status == 1
        st.session_state.x[recruits] += np.random.normal(0, 0.5, recruits.sum())
        st.session_state.y[recruits] += np.random.normal(0, 0.7, recruits.sum())
        
        # AFFICHAGE TOUTES LES 3 FRAMES (au lieu de 2)
        if step % 3 == 0 or step == 29:
            with placeholder.container():
                fig = draw_map(st.session_state.x, st.session_state.y, 
                               st.session_state.status, step, wind_dir, wind_power)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
        
        time.sleep(0.05)  # Plus lent mais stable
    
    progress.empty()
    
    rec = int(np.sum(st.session_state.status == 1))
    ech = int(np.sum(st.session_state.status == 2))
    
    col1, col2 = st.columns(2)
    col1.metric("🦀 Recrutés", rec)
    col2.metric("❌ Échoués", ech)

else:
    fig = draw_map(st.session_state.x, st.session_state.y, 
                   st.session_state.status, 0, wind_dir, wind_power)
    placeholder.pyplot(fig, use_container_width=True)
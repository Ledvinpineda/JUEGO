# JuegoLedvin.py

import pygame
import pygame.freetype
import random
import math
import time
import json
import os
import sys
from datetime import datetime

from powerups import PowerUp, ShieldPowerUp, DoubleScorePowerUp
from score_manager import ScoreManager
from keyboard_layout_manager import KeyboardLayoutManager
from render_utils import render_text_gradient
from game_session import GameSession

# ========================
# CONFIGURACIÓN INICIAL
# ========================
pygame.init()
pygame.freetype.init()
pygame.mixer.init()
clock = pygame.time.Clock()

info = pygame.display.Info()
ANCHO, ALTO = info.current_w, info.current_h
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("SpeedType Animated")

# ========================
# COLORES Y FUENTES
# ========================
NEGRO = (0, 0, 0); BLANCO = (255, 255, 255); ROJO = (255, 0, 0); VERDE = (0, 255, 0)
GRIS_OSCURO = (50, 50, 50); GRIS_CLARO = (100, 100, 100); AMARILLO = (255, 255, 0)
colores_disponibles = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0), (128, 0, 128)]
fuentes_disponibles = ["arial", "comicsansms", "couriernew", "verdana"]

# ========================
# ESTILOS NEÓN
# ========================
ESTILO_NEON = "fucsia_cian"
estilos_neon = {
    "fucsia_cian": {"top": (255, 0, 255), "bottom": (0, 255, 255)},
    "verde_azul": {"top": (57, 255, 20), "bottom": (0, 255, 255)},
    "rosa_naranja": {"top": (255, 20, 147), "bottom": (255, 140, 0)},
}
COLOR_GRADIENTE_TOP = estilos_neon[ESTILO_NEON]["top"]
COLOR_GRADIENTE_BOTTOM = estilos_neon[ESTILO_NEON]["bottom"]
COLOR_CONTORNO = (0, 0, 0)
FUENTE_LOGO_STYLE = "Impact"

# ========================
# CARGA DE RECURSOS
# ========================
try:
    ruta_fondo = os.path.join(os.path.dirname(__file__), "Fondo2.png")
    fondo_img = pygame.image.load(ruta_fondo).convert()
    fondo_img = pygame.transform.scale(fondo_img, (ANCHO, ALTO))
except: fondo_img = pygame.Surface((ANCHO, ALTO)); fondo_img.fill(NEGRO)

try:
    ruta_fondo_pausa = os.path.join(os.path.dirname(__file__), "Fondo2.png")
    fondo_pausa_img = pygame.image.load(ruta_fondo_pausa).convert()
    fondo_pausa_img = pygame.transform.scale(fondo_pausa_img, (ANCHO, ALTO))
except Exception as e: print(f"Error al cargar el fondo de pausa: {e}"); fondo_pausa_img = None

estrellas = [[random.randint(0, ANCHO), random.randint(0, ALTO), random.uniform(0.5, 1.5)] for _ in range(100)]
particulas = []
music_loaded = False
try:
    acierto_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "acierto.wav"))
    fallo_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "fallo.wav"))
    game_over_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "game_over.wav"))
    pygame.mixer.music.load(os.path.join(os.path.dirname(__file__), "musica_fondo.mp3"))
    pygame.mixer.music.set_volume(0.5)
    powerup_activate_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "powerup.mp3"))
    shield_hit_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "letraescudo.mp3"))
    double_score_activate_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "doblep.mp3"))
    music_loaded = True
except Exception as e:
    print(f"Error cargando música o sonidos: {e}")
    acierto_sound, fallo_sound, game_over_sound, powerup_activate_sound, shield_hit_sound, double_score_activate_sound = [None]*6

powerup_icons = {}
icon_size = 60
try:
    powerup_icons["ralentizar"] = pygame.transform.scale(pygame.image.load(os.path.join(os.path.dirname(__file__), "caracol.png")).convert_alpha(), (icon_size, icon_size))
    powerup_icons["escudo"] = pygame.transform.scale(pygame.image.load(os.path.join(os.path.dirname(__file__), "escudo.png")).convert_alpha(), (icon_size, icon_size))
    powerup_icons["doble_puntuacion"] = pygame.transform.scale(pygame.image.load(os.path.join(os.path.dirname(__file__), "dos.png")).convert_alpha(), (icon_size, icon_size))
except Exception as e:
    print(f"Error cargando iconos de power-ups: {e}")
    for p_type in ["ralentizar", "escudo", "doble_puntuacion"]:
        powerup_icons[p_type] = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)

# --- Cargar imágenes de los generadores de letras ---
spawner_icons = {}
spawner_icon_size = (80, 80) # Tamaño para el avión y el icono lateral
try:
    spawner_icons["avion"] = pygame.image.load(os.path.join(os.path.dirname(__file__), "helicoptero.png")).convert_alpha()
    spawner_icons["avion"] = pygame.transform.scale(spawner_icons["avion"], spawner_icon_size)
    spawner_icons["icono_lateral"] = pygame.image.load(os.path.join(os.path.dirname(__file__), "vehiculo.png")).convert_alpha()
    spawner_icons["icono_lateral"] = pygame.transform.scale(spawner_icons["icono_lateral"], spawner_icon_size)
except Exception as e:
    print(f"Error cargando iconos de generadores: {e}")
    spawner_icons["avion"] = pygame.Surface(spawner_icon_size, pygame.SRCALPHA)
    spawner_icons["icono_lateral"] = pygame.Surface(spawner_icon_size, pygame.SRCALPHA)

# ========================
# FUNCIONES DE UI Y UTILIDADES
# ========================
def dibujar_estrellas(velocidad=1):
    for estrella in estrellas:
        estrella[1] += estrella[2] * velocidad
        if estrella[1] > ALTO:
            estrella[0] = random.randint(0, ANCHO); estrella[1] = 0
        pygame.draw.circle(pantalla, BLANCO, (int(estrella[0]), int(estrella[1])), 2)

def crear_particulas(x, y, color):
    for _ in range(10):
        particulas.append({'x': x, 'y': y, 'vx': random.uniform(-2, 2), 'vy': random.uniform(-2, 2), 'radius': random.randint(2, 5), 'color': color, 'life': 30})

def actualizar_y_dibujar_particulas():
    global particulas
    particulas_vivas = []
    for p in particulas:
        p['x'] += p['vx']; p['y'] += p['vy']; p['radius'] -= 0.1; p['life'] -= 1
        if p['life'] > 0 and p['radius'] > 0:
            pygame.draw.circle(pantalla, p['color'], (int(p['x']), int(p['y'])), int(p['radius']))
            particulas_vivas.append(p)
    particulas = particulas_vivas

def guardar_config(fuente, tam, color):
    with open("config.json", "w") as f: json.dump({"fuente": fuente, "tam": tam, "color": list(color)}, f)

def cargar_config():
    if os.path.exists("config.json"):
        try:
            with open("config.json") as f: return json.load(f)
        except Exception: return None
    return None

def guardar_partida(estado_juego, game_mode, timestamp_a_actualizar=None):
    saved_games = cargar_partida()
    if timestamp_a_actualizar:
        for game in saved_games:
            if game.get("timestamp") == timestamp_a_actualizar:
                game.update({"state": estado_juego, "timestamp": datetime.now().isoformat()}); break
        else: timestamp_a_actualizar = None
    if not timestamp_a_actualizar:
        saved_games.append({"timestamp": datetime.now().isoformat(), "mode": game_mode, "state": estado_juego})
    saved_games.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    with open("partida_guardada.json", "w") as f: json.dump(saved_games[:5], f, indent=4)

def cargar_partida():
    if os.path.exists("partida_guardada.json"):
        try:
            with open("partida_guardada.json", "r") as f:
                content = f.read()
                data = json.loads(content) if content else []
                if isinstance(data, list): return [s for s in data if isinstance(s, dict) and 'timestamp' in s]
                elif isinstance(data, dict): return [data] if 'timestamp' in data else []
                return []
        except Exception: return []
    return []

def eliminar_partida_guardada(timestamp_a_eliminar):
    saved_games = [g for g in cargar_partida() if g.get("timestamp") != timestamp_a_eliminar]
    with open("partida_guardada.json", "w") as f: json.dump(saved_games, f, indent=4)

def cargar_highscores():
    if not os.path.exists("highscores.json"): return []
    try:
        with open("highscores.json", "r") as f: return sorted(json.load(f), key=lambda x: x['score'], reverse=True)
    except Exception: return []

def guardar_highscores(scores):
    with open("highscores.json", "w") as f: json.dump(scores, f, indent=4)

def check_if_highscore(score):
    highscores = cargar_highscores()
    if not highscores: return score > 0
    return len(highscores) < 5 or (score > 0 and score >= highscores[-1]['score'])

class Button:
    def __init__(self, x, y, width, height, text, font_obj, color, hover_color, text_color=BLANCO, border_color=BLANCO, border_thickness=3, border_radius=10):
        self.rect = pygame.Rect(x, y, width, height)
        self.text, self.font = text, font_obj
        self.color, self.hover_color = color, hover_color
        self.border_color, self.border_thickness, self.border_radius = border_color, border_thickness, border_radius
        self.is_hovered = False; self.use_logo_style = False
        self.logo_style_gradient_colors = [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM]
        self.logo_style_border_color, self.logo_style_border_thickness = COLOR_CONTORNO, 2
    def set_logo_style(self, enable=True, **kwargs):
        self.use_logo_style = enable
        self.logo_style_gradient_colors=kwargs.get("gradient_colors", self.logo_style_gradient_colors)
    def draw(self, surface):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_thickness, border_radius=self.border_radius)
        if self.use_logo_style:
            render_text_gradient(self.font, self.text, self.rect, surface, self.logo_style_gradient_colors, self.logo_style_border_color, self.logo_style_border_thickness)
        else:
            text_surface, text_rect = self.font.render(self.text, BLANCO); text_rect.center = self.rect.center; surface.blit(text_surface, text_rect)
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION: self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered: return True
        return False

def pantalla_intro():
    start_time = time.time()
    if music_loaded: pygame.mixer.music.play(-1, 0.0)
    logo_img = None
    try: logo_img = pygame.transform.scale(pygame.image.load(os.path.join(os.path.dirname(__file__), "Logotipo.png")).convert_alpha(), (ANCHO, ALTO))
    except Exception as e: print(f"Error al cargar Logotipo.png: {e}")
    while True:
        elapsed_time = time.time() - start_time
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN and (evento.key == pygame.K_RETURN or evento.key == pygame.K_SPACE): return
        pantalla.blit(fondo_img, (0, 0))
        if elapsed_time > 4.5: return
        alpha = 255
        if elapsed_time < 1.5: alpha = int(255 * (elapsed_time / 1.5))
        elif elapsed_time > 3.0: alpha = int(255 * ((4.5 - elapsed_time) / 1.5))
        if logo_img: logo_img.set_alpha(max(0, min(255, alpha))); pantalla.blit(logo_img, (0, 0))
        pygame.display.flip(); clock.tick(60)

def pantalla_configuracion(config):
    tam = config["tam"]; nombre_fuente = config["fuente"]; color = tuple(config["color"])
    idx_fuente = fuentes_disponibles.index(nombre_fuente) if nombre_fuente in fuentes_disponibles else 0
    idx_color = colores_disponibles.index(color) if color in colores_disponibles else 0
    fuente_guardar_btn = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 22)
    btn_guardar = Button(ANCHO//2 - 130, ALTO - 100, 260, 60, "GUARDAR Y CONTINUAR", fuente_guardar_btn, GRIS_OSCURO, GRIS_CLARO); btn_guardar.set_logo_style(True)
    y_base_botones = 150
    btn_tam_left = Button(ANCHO//2-200, y_base_botones+50, 40, 40, "<", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_tam_right = Button(ANCHO//2+160, y_base_botones+50, 40, 40, ">", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_fuente_left = Button(ANCHO//2-200, y_base_botones+100, 40, 40, "<", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_fuente_right = Button(ANCHO//2+160, y_base_botones+100, 40, 40, ">", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_color_left = Button(ANCHO//2-200, y_base_botones+150, 40, 40, "<", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_color_right = Button(ANCHO//2+160, y_base_botones+150, 40, 40, ">", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if btn_tam_left.handle_event(evento): tam = max(30, tam - 5)
            elif btn_tam_right.handle_event(evento): tam = min(200, tam + 5)
            elif btn_fuente_left.handle_event(evento): idx_fuente=(idx_fuente-1)%len(fuentes_disponibles); nombre_fuente=fuentes_disponibles[idx_fuente]
            elif btn_fuente_right.handle_event(evento): idx_fuente=(idx_fuente+1)%len(fuentes_disponibles); nombre_fuente=fuentes_disponibles[idx_fuente]
            elif btn_color_left.handle_event(evento): idx_color=(idx_color-1)%len(colores_disponibles); color=colores_disponibles[idx_color]
            elif btn_color_right.handle_event(evento): idx_color=(idx_color+1)%len(colores_disponibles); color=colores_disponibles[idx_color]
            elif btn_guardar.handle_event(evento) or (evento.type==pygame.KEYDOWN and evento.key==pygame.K_RETURN):
                return nombre_fuente, tam, color
        pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas()
        y_base=100; separacion=50
        render_text_gradient(pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50), "CONFIGURACIÓN", pygame.Rect(0,y_base-50,ANCHO,50), pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)
        fuente_ui_text = pygame.freetype.SysFont("arial", 40)
        texto_tam, _ = fuente_ui_text.render(f"Tamaño: {tam}", BLANCO); pantalla.blit(texto_tam, (ANCHO//2-texto_tam.get_width()//2, y_base+separacion))
        texto_fuente, _ = fuente_ui_text.render(f"Fuente: {nombre_fuente}", BLANCO); pantalla.blit(texto_fuente, (ANCHO//2-texto_fuente.get_width()//2, y_base+2*separacion))
        texto_color, _ = fuente_ui_text.render(f"Color:", color); pantalla.blit(texto_color, (ANCHO//2-texto_color.get_width()//2, y_base+3*separacion))
        fuente_letras_preview = pygame.freetype.SysFont(nombre_fuente, tam)
        texto_prev_surf, texto_prev_rect = fuente_letras_preview.render("A", color)
        texto_prev_rect.center = (ANCHO//2, y_base + 4*separacion + 50); pantalla.blit(texto_prev_surf, texto_prev_rect)
        btn_tam_left.draw(pantalla); btn_tam_right.draw(pantalla); btn_fuente_left.draw(pantalla); btn_fuente_right.draw(pantalla)
        btn_color_left.draw(pantalla); btn_color_right.draw(pantalla); btn_guardar.draw(pantalla)
        pygame.display.flip(); clock.tick(60)

def pantalla_menu_principal():
    # --- LÍNEA AÑADIDA ---
    # Asegúrate de que la música esté sonando cuando estemos en el menú principal
    if music_loaded and not pygame.mixer.music.get_busy():
        pygame.mixer.music.play(-1)
    # ---------------------

    btn_y_start, btn_spacing = ALTO // 2 - 50, 80
    fuente_opciones = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    btn_modos_juego = Button(ANCHO//2-140, btn_y_start, 280, 60, "JUGAR", fuente_opciones, GRIS_OSCURO, GRIS_CLARO)
    btn_puntuaciones = Button(ANCHO//2-140, btn_y_start + btn_spacing, 280, 60, "PUNTUACIONES", fuente_opciones, GRIS_OSCURO, GRIS_CLARO)
    btn_cargar = Button(ANCHO//2-140, btn_y_start + 2 * btn_spacing, 280, 60, "CARGAR PARTIDA", fuente_opciones, GRIS_OSCURO, GRIS_CLARO)
    btn_config = Button(ANCHO//2-140, btn_y_start + 3 * btn_spacing, 280, 60, "CONFIGURACIÓN", fuente_opciones, GRIS_OSCURO, GRIS_CLARO)
    btn_salir = Button(ANCHO//2-140, btn_y_start + 4 * btn_spacing, 280, 60, "SALIR", fuente_opciones, GRIS_OSCURO, GRIS_CLARO)
    botones = [btn_modos_juego, btn_puntuaciones, btn_cargar, btn_config, btn_salir]
    for btn in botones: btn.set_logo_style(True)
    logo_img = None
    try: logo_img = pygame.image.load(os.path.join(os.path.dirname(__file__), "remove.png")).convert_alpha()
    except Exception: pass
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if btn_modos_juego.handle_event(evento): return "seleccion_modo"
            if btn_puntuaciones.handle_event(evento): return "highscores"
            if btn_cargar.handle_event(evento): return "cargar_partida"
            if btn_config.handle_event(evento): return "configuracion"
            if btn_salir.handle_event(evento) or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
                if confirmar_salida(): pygame.quit(); sys.exit()
        pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas(0.5)
        if logo_img:
            logo_rect = logo_img.get_rect(center=(ANCHO // 2, ALTO // 4)); pantalla.blit(logo_img, logo_rect)
        else:
            fuente_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 80)
            rect_titulo = pygame.Rect(0, ALTO // 4 - 50, ANCHO, 100)
            render_text_gradient(fuente_titulo, "SPEEDTYPE", rect_titulo, pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 4)
        for btn in botones: btn.draw(pantalla)
        pygame.display.flip(); clock.tick(60)

def pantalla_seleccion_modo_juego():
    fuente_opciones = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    btn_arcane = Button(ANCHO//2-150, ALTO//2-100, 300, 70, "MODO ARCANE (1P)", fuente_opciones, GRIS_OSCURO, GRIS_CLARO); btn_arcane.set_logo_style(True)
    btn_versus = Button(ANCHO//2-150, ALTO//2-10, 300, 70, "MODO VERSUS (2P)", fuente_opciones, GRIS_OSCURO, GRIS_CLARO); btn_versus.set_logo_style(True)
    btn_volver = Button(ANCHO//2-150, ALTO//2+150, 300, 70, "VOLVER", fuente_opciones, GRIS_OSCURO, GRIS_CLARO); btn_volver.set_logo_style(True)
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if btn_arcane.handle_event(evento): return "arcane"
            if btn_versus.handle_event(evento): return "versus"
            if btn_volver.handle_event(evento) or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE): return "volver_menu"
        pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas(0.5)
        render_text_gradient(pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 60), "SELECCIONAR MODO", pygame.Rect(0, ALTO//4-50, ANCHO, 100), pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 4)
        btn_arcane.draw(pantalla); btn_versus.draw(pantalla); btn_volver.draw(pantalla)
        pygame.display.flip(); clock.tick(60)

def pantalla_configuracion_arcane():
    fuente_titulo_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
    fuente_opciones_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    fuente_fallos_num = pygame.freetype.SysFont("arial", 60)
    fallos_disponibles = [5, 10, 15, 20]; fallos_seleccionado_idx = 1
    btn_fallos_left = Button(ANCHO//2-200, ALTO//2-30, 40, 40, "<", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_fallos_right = Button(ANCHO//2+160, ALTO//2-30, 40, 40, ">", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_iniciar = Button(ANCHO//2-150, ALTO//2+100, 300, 70, "INICIAR ARCANE", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO); btn_iniciar.set_logo_style(True)
    btn_volver = Button(ANCHO//2-150, ALTO//2+200, 300, 70, "VOLVER", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO); btn_volver.set_logo_style(True)
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if btn_fallos_left.handle_event(evento): fallos_seleccionado_idx = (fallos_seleccionado_idx - 1) % len(fallos_disponibles)
            if btn_fallos_right.handle_event(evento): fallos_seleccionado_idx = (fallos_seleccionado_idx + 1) % len(fallos_disponibles)
            if btn_iniciar.handle_event(evento): return fallos_disponibles[fallos_seleccionado_idx]
            if btn_volver.handle_event(evento): return "volver_seleccion_modo"
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_LEFT: fallos_seleccionado_idx = (fallos_seleccionado_idx - 1) % len(fallos_disponibles)
                elif evento.key == pygame.K_RIGHT: fallos_seleccionado_idx = (fallos_seleccionado_idx + 1) % len(fallos_disponibles)
                elif evento.key == pygame.K_RETURN: return fallos_disponibles[fallos_seleccionado_idx]
                elif evento.key == pygame.K_ESCAPE: return "volver_seleccion_modo"
        pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas(0.5)
        render_text_gradient(fuente_titulo_estilo, "LÍMITE DE FALLOS", pygame.Rect(0,ALTO//4-50,ANCHO,100), pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)
        fallos_texto, fallos_rect = fuente_fallos_num.render(f"{fallos_disponibles[fallos_seleccionado_idx]} fallos", BLANCO); fallos_rect.center = (ANCHO//2, ALTO//2-10); pantalla.blit(fallos_texto, fallos_rect)
        btn_fallos_left.draw(pantalla); btn_fallos_right.draw(pantalla); btn_iniciar.draw(pantalla); btn_volver.draw(pantalla)
        pygame.display.flip(); clock.tick(60)

def pantalla_configuracion_versus():
    fuente_titulo_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
    fuente_opciones_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    fuente_tiempo_num = pygame.freetype.SysFont("arial", 60)
    tiempos_disponibles = [1, 2, 3, 5]; tiempo_seleccionado_idx = 0
    btn_tiempo_left = Button(ANCHO//2-200, ALTO//2-30, 40, 40, "<", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_tiempo_right = Button(ANCHO//2+160, ALTO//2-30, 40, 40, ">", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_iniciar = Button(ANCHO//2-150, ALTO//2+100, 300, 70, "INICIAR VERSUS", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO); btn_iniciar.set_logo_style(True)
    btn_volver = Button(ANCHO//2-150, ALTO//2+200, 300, 70, "VOLVER", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO); btn_volver.set_logo_style(True)
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if btn_tiempo_left.handle_event(evento): tiempo_seleccionado_idx = (tiempo_seleccionado_idx - 1) % len(tiempos_disponibles)
            if btn_tiempo_right.handle_event(evento): tiempo_seleccionado_idx = (tiempo_seleccionado_idx + 1) % len(tiempos_disponibles)
            if btn_iniciar.handle_event(evento): return tiempos_disponibles[tiempo_seleccionado_idx]
            if btn_volver.handle_event(evento): return "volver_seleccion_modo"
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_LEFT: tiempo_seleccionado_idx = (tiempo_seleccionado_idx - 1) % len(tiempos_disponibles)
                elif evento.key == pygame.K_RIGHT: tiempo_seleccionado_idx = (tiempo_seleccionado_idx + 1) % len(tiempos_disponibles)
                elif evento.key == pygame.K_RETURN: return tiempos_disponibles[tiempo_seleccionado_idx]
                elif evento.key == pygame.K_ESCAPE: return "volver_seleccion_modo"
        pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas(0.5)
        render_text_gradient(fuente_titulo_estilo, "LÍMITE DE TIEMPO", pygame.Rect(0,ALTO//4-50,ANCHO,100), pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)
        tiempo_texto, tiempo_rect = fuente_tiempo_num.render(f"{tiempos_disponibles[tiempo_seleccionado_idx]} min", BLANCO); tiempo_rect.center = (ANCHO//2, ALTO//2-10); pantalla.blit(tiempo_texto, tiempo_rect)
        btn_tiempo_left.draw(pantalla); btn_tiempo_right.draw(pantalla); btn_iniciar.draw(pantalla); btn_volver.draw(pantalla)
        pygame.display.flip(); clock.tick(60)

def pantalla_de_pausa():
    fuente_pausa_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 60)
    btn_reanudar = Button(ANCHO//2-150, ALTO//2-100, 300, 70, "REANUDAR", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO); btn_reanudar.set_logo_style(True)
    btn_guardar_salir = Button(ANCHO//2-150, ALTO//2, 300, 70, "GUARDAR Y SALIR", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO); btn_guardar_salir.set_logo_style(True)
    btn_salir_sin_guardar = Button(ANCHO//2-150, ALTO//2+100, 300, 70, "SALIR SIN GUARDAR", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO); btn_salir_sin_guardar.set_logo_style(True)
    if music_loaded: pygame.mixer.music.pause()
    superficie_oscura = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); superficie_oscura.fill((0, 0, 0, 180))
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if btn_reanudar.handle_event(evento) or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
                if music_loaded: pygame.mixer.music.unpause()
                return "reanudar"
            if btn_guardar_salir.handle_event(evento): return "guardar_y_salir"
            if btn_salir_sin_guardar.handle_event(evento): return "salir_sin_guardar"
        if fondo_pausa_img: pantalla.blit(fondo_pausa_img, (0,0))
        pantalla.blit(superficie_oscura, (0,0))
        render_text_gradient(fuente_pausa_titulo, "PAUSA", pygame.Rect(0, ALTO//2-200, ANCHO, 70), pantalla, [BLANCO, (200,200,200)], COLOR_CONTORNO, 3)
        btn_reanudar.draw(pantalla); btn_guardar_salir.draw(pantalla); btn_salir_sin_guardar.draw(pantalla)
        pygame.display.flip(); clock.tick(60)

def pantalla_fin_juego(score, aciertos, fallos, num_jugadores, scores_j1=None, scores_j2=None):
    fuente_ui_go_text = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 40)
    fuente_ui_go_stats = pygame.freetype.SysFont("arial", 30)
    fuente_ui_go_btns = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    if num_jugadores == 1:
        btn_reiniciar = Button(ANCHO // 2 - 150, ALTO // 2 + 80, 140, 60, "REINICIAR", fuente_ui_go_btns, GRIS_OSCURO, GRIS_CLARO); btn_reiniciar.set_logo_style(True)
        btn_salir_go = Button(ANCHO // 2 + 10, ALTO // 2 + 80, 140, 60, "SALIR", fuente_ui_go_btns, GRIS_OSCURO, GRIS_CLARO); btn_salir_go.set_logo_style(True)
        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
                if btn_reiniciar.handle_event(evento): return "reiniciar"
                if btn_salir_go.handle_event(evento): return "menu_principal"
            pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas()
            prec = (aciertos / (aciertos + fallos)) * 100 if (aciertos + fallos) > 0 else 0
            render_text_gradient(fuente_ui_go_text, "¡GAME OVER!", pygame.Rect(0, ALTO//2 - 100, ANCHO, 50), pantalla, [ROJO, (255,100,0)], COLOR_CONTORNO, 3)
            t2, r2 = fuente_ui_go_stats.render(f"Puntaje: {score}", BLANCO); r2.center = (ANCHO//2, ALTO//2 - 20); pantalla.blit(t2, r2)
            t3, r3 = fuente_ui_go_stats.render(f"Aciertos: {aciertos} Fallos: {fallos} Precisión: {prec:.2f}%", BLANCO); r3.center = (ANCHO//2, ALTO//2 + 20); pantalla.blit(t3, r3)
            btn_reiniciar.draw(pantalla); btn_salir_go.draw(pantalla)
            pygame.display.flip(); clock.tick(60)
    else:
        fuente_resultado_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 60)
        fuente_resultado_texto = pygame.freetype.SysFont("arial", 40)
        fuente_botones = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
        if scores_j1 > scores_j2: ganador, color_ganador = "JUGADOR 1", VERDE
        elif scores_j2 > scores_j1: ganador, color_ganador = "JUGADOR 2", AMARILLO
        else: ganador, color_ganador = "EMPATE", BLANCO
        btn_reiniciar = Button(ANCHO//2-160, ALTO-160, 150, 60, "REINICIAR", fuente_botones, GRIS_OSCURO, GRIS_CLARO); btn_reiniciar.set_logo_style(True)
        btn_menu = Button(ANCHO//2+10, ALTO-160, 150, 60, "MENÚ", fuente_botones, GRIS_OSCURO, GRIS_CLARO); btn_menu.set_logo_style(True)
        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
                if btn_reiniciar.handle_event(evento): return "reiniciar"
                if btn_menu.handle_event(evento) or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE): return "menu_principal"
            pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas()
            render_text_gradient(fuente_resultado_titulo, "RESULTADOS FINALES", pygame.Rect(0, 100, ANCHO, 80), pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 4)
            surf_j1, _ = fuente_resultado_texto.render(f"JUGADOR 1: {scores_j1} pts", VERDE); pantalla.blit(surf_j1, (ANCHO//4 - surf_j1.get_width()//2, 200))
            surf_j2, _ = fuente_resultado_texto.render(f"JUGADOR 2: {scores_j2} pts", AMARILLO); pantalla.blit(surf_j2, (3 * ANCHO//4 - surf_j2.get_width()//2, 200))
            if ganador != "EMPATE": pygame.draw.rect(pantalla, color_ganador, pygame.Rect((ANCHO//4 if ganador == "JUGADOR 1" else 3*ANCHO//4) - 160, 190, 320, 60), 4, border_radius=10)
            fuente_ganador = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
            render_text_gradient(fuente_ganador, f"GANADOR: {ganador}", pygame.Rect(0, 320, ANCHO, 80), pantalla, [color_ganador, BLANCO], COLOR_CONTORNO, 3)
            btn_reiniciar.draw(pantalla); btn_menu.draw(pantalla)
            pygame.display.flip(); clock.tick(60)

def confirmar_salida():
    if music_loaded and pygame.mixer.music.get_busy(): pygame.mixer.music.pause()
    caja_rect = pygame.Rect((ANCHO - 400) // 2, (ALTO - 200) // 2, 400, 200)
    btn_si = Button(caja_rect.x+50, caja_rect.y+140, 100, 40, "SÍ", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 20), GRIS_OSCURO, GRIS_CLARO); btn_si.set_logo_style(True)
    btn_no = Button(caja_rect.x+250, caja_rect.y+140, 100, 40, "NO", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 20), GRIS_OSCURO, GRIS_CLARO); btn_no.set_logo_style(True)
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if btn_si.handle_event(evento): return True
            if btn_no.handle_event(evento):
                if music_loaded: pygame.mixer.music.unpause()
                return False
        pantalla.blit(fondo_img, (0,0)); dibujar_estrellas()
        pygame.draw.rect(pantalla, NEGRO, caja_rect, border_radius=15); pygame.draw.rect(pantalla, BLANCO, caja_rect, 3, border_radius=15)
        mensaje_texto, mensaje_rect = pygame.freetype.SysFont("arial", 25).render("¿Estás seguro de que quieres salir?", BLANCO); mensaje_rect.center = (caja_rect.centerx, caja_rect.y + 40); pantalla.blit(mensaje_texto, mensaje_rect)
        btn_si.draw(pantalla); btn_no.draw(pantalla)
        pygame.display.flip(); clock.tick(60)

def mostrar_conteo_regresivo(segundos, fuente_obj, color):
    superficie_oscura = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); superficie_oscura.fill((0, 0, 0, 180))
    fuente_conteo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 100)
    for i in range(segundos, 0, -1):
        pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas(0.5); pantalla.blit(superficie_oscura, (0,0))
        render_text_gradient(fuente_conteo, str(i), pygame.Rect(0,0,ANCHO,ALTO), pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 5)
        pygame.display.flip(); pygame.time.delay(1000)

def pantalla_ingresar_nombre(score):
    nombre_jugador = ""; fuente_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50); fuente_input = pygame.freetype.SysFont("arial", 60); fuente_instr = pygame.freetype.SysFont("arial", 25)
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN and len(nombre_jugador) > 0:
                    highscores = cargar_highscores(); highscores.append({"nombre": nombre_jugador.upper(), "score": score})
                    guardar_highscores(sorted(highscores, key=lambda x: x['score'], reverse=True)[:5]); return
                elif evento.key == pygame.K_BACKSPACE: nombre_jugador = nombre_jugador[:-1]
                elif len(nombre_jugador) < 3 and evento.unicode.isalpha(): nombre_jugador += evento.unicode.upper()
        pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas()
        render_text_gradient(fuente_titulo, "¡NUEVO RÉCORD!", pygame.Rect(0, ALTO//2 - 150, ANCHO, 50), pantalla, [AMARILLO, BLANCO], COLOR_CONTORNO, 3)
        instr_surf, instr_rect = fuente_instr.render("Ingresa tus iniciales (3 letras) y presiona ENTER", BLANCO); instr_rect.center = (ANCHO//2, ALTO//2 - 80); pantalla.blit(instr_surf, instr_rect)
        caja_rect = pygame.Rect(ANCHO//2 - 100, ALTO//2 - 40, 200, 80)
        pygame.draw.rect(pantalla, GRIS_OSCURO, caja_rect, border_radius=10); pygame.draw.rect(pantalla, BLANCO, caja_rect, 3, border_radius=10)
        nombre_surf, nombre_rect = fuente_input.render(nombre_jugador, BLANCO); nombre_rect.center = caja_rect.center; pantalla.blit(nombre_surf, nombre_rect)
        pygame.display.flip(); clock.tick(60)

def pantalla_highscores():
    fuente_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 60); fuente_score = pygame.freetype.SysFont("arial", 40)
    fuente_btn = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    highscores = cargar_highscores()
    btn_volver = Button(ANCHO//2-150, ALTO-100, 300, 70, "VOLVER", fuente_btn, GRIS_OSCURO, GRIS_CLARO); btn_volver.set_logo_style(True)
    btn_limpiar = Button(ANCHO//2-150, ALTO-180, 300, 70, "LIMPIAR PUNTUACIONES", fuente_btn, ROJO, (200,0,0)); btn_limpiar.set_logo_style(True, gradient_colors=[ROJO, (255,100,100)], border_color=NEGRO)
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if btn_volver.handle_event(evento) or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE): return
            if btn_limpiar.handle_event(evento):
                if os.path.exists("highscores.json"):
                    os.remove("highscores.json"); highscores = []
                    print("Archivo de puntuaciones eliminado.")
        pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas()
        render_text_gradient(fuente_titulo, "PUNTUACIONES MÁS ALTAS", pygame.Rect(0,100,ANCHO,100), pantalla, [AMARILLO, BLANCO], COLOR_CONTORNO, 4)
        if not highscores:
            texto, rect = fuente_score.render("Aún no hay récords.", BLANCO); rect.center = (ANCHO//2, ALTO//2); pantalla.blit(texto, rect)
        else:
            for i, entry in enumerate(highscores):
                texto, rect = fuente_score.render(f"{i+1}. {entry['nombre']} - {entry['score']}", BLANCO); rect.center = (ANCHO//2, 200 + i*60); pantalla.blit(texto, rect)
        btn_volver.draw(pantalla); btn_limpiar.draw(pantalla)
        pygame.display.flip(); clock.tick(60)

def pantalla_seleccionar_partida(saved_games):
    fuente_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
    fuente_opciones = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    btn_volver = Button(ANCHO//2-150, ALTO-100, 300, 70, "VOLVER", fuente_opciones, GRIS_OSCURO, GRIS_CLARO); btn_volver.set_logo_style(True)
    btns = []
    for i, save in enumerate(saved_games):
        timestamp_dt = datetime.fromisoformat(save['timestamp']); display_time = timestamp_dt.strftime("%Y-%m-%d %H:%M")
        mode_display = "Arcane (1P)" if save['mode'] == "arcane" else "Versus (2P)"
        btn_text = f"{i+1}. {mode_display} - {display_time}"
        load_btn = Button(ANCHO//2-250, 150+i*80, 500, 60, btn_text, pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO); load_btn.set_logo_style(False)
        delete_btn = Button(load_btn.rect.right+10, 150+i*80, 60, 60, "X", pygame.freetype.SysFont("arial", 30), (150,0,0), (255,0,0)); delete_btn.set_logo_style(False)
        btns.append((load_btn, delete_btn, save))
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            for load_btn, delete_btn, save_data in btns:
                if load_btn.handle_event(evento): return save_data
                if delete_btn.handle_event(evento): eliminar_partida_guardada(save_data['timestamp']); return "refresh"
            if btn_volver.handle_event(evento) or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE): return "volver_menu"
        pantalla.blit(fondo_img, (0, 0)); dibujar_estrellas(0.5)
        render_text_gradient(fuente_titulo, "CARGAR PARTIDA", pygame.Rect(0, 50, ANCHO, 100), pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 4)
        if not saved_games:
            texto, rect = pygame.freetype.SysFont("arial", 25).render("No hay partidas guardadas.", BLANCO); rect.center = (ANCHO//2, ALTO//2); pantalla.blit(texto, rect)
        for load_btn, delete_btn, _ in btns:
            load_btn.draw(pantalla); delete_btn.draw(pantalla)
        btn_volver.draw(pantalla)
        pygame.display.flip(); clock.tick(60)

# ========================
# EJECUCIÓN PRINCIPAL
# ========================
if __name__ == '__main__':
    pantalla_intro()
    
    config = cargar_config()
    if not config:
        config = {"fuente": fuentes_disponibles[0], "tam": 60, "color": colores_disponibles[0]}
    
    config["color"] = tuple(config["color"])

    while True:
        accion = pantalla_menu_principal()
        
        game_options = None; initial_state = None; save_timestamp = None; resultado_juego = None
        
        if accion == "seleccion_modo":
            modo_seleccionado = pantalla_seleccion_modo_juego()
            if modo_seleccionado == "arcane":
                fallos_limit = pantalla_configuracion_arcane()
                if fallos_limit != "volver_seleccion_modo": game_options = {"num_jugadores": 1, "initial_speed": 1.5, "count_wrong_key_faults": True, "time_limit_seconds": 0, "fallos_limit": fallos_limit}
            elif modo_seleccionado == "versus":
                time_limit_minutes = pantalla_configuracion_versus()
                if time_limit_minutes != "volver_seleccion_modo": game_options = {"num_jugadores": 2, "initial_speed": 2.0, "count_wrong_key_faults": True, "time_limit_seconds": time_limit_minutes * 60, "fallos_limit": 999}
        elif accion == "highscores": pantalla_highscores(); continue
        elif accion == "configuracion":
            nombre_fuente, tam, color = pantalla_configuracion(config)
            config = {"fuente": nombre_fuente, "tam": tam, "color": color}
            guardar_config(nombre_fuente, tam, color); continue
        elif accion == "cargar_partida":
            while True:
                saved_games_list = cargar_partida()
                selected_save_data = pantalla_seleccionar_partida(saved_games_list)
                if selected_save_data == "refresh": continue
                if selected_save_data and selected_save_data != "volver_menu":
                    initial_state = selected_save_data["state"]
                    save_timestamp = selected_save_data["timestamp"]
                    game_options = {
                        "num_jugadores": 1 if selected_save_data["mode"] == "arcane" else 2,
                        "initial_speed": initial_state.get("velocidad", 1.5),
                        "count_wrong_key_faults": True,
                        "fallos_limit": initial_state.get("fallos_limit", 10),
                        "time_limit_seconds": initial_state.get("time_limit_seconds", 0)
                    }
                break

        if game_options:
            current_config = {"fuente": config["fuente"], "tam": config["tam"], "color": config["color"]}
            game_session = GameSession(sys.modules[__name__], current_config, game_options, initial_state, save_timestamp)
            resultado_juego = game_session.run()

            while resultado_juego == "reiniciar":
                if music_loaded and not pygame.mixer.music.get_busy(): pygame.mixer.music.play(-1)
                game_session = GameSession(sys.modules[__name__], current_config, game_options)
                resultado_juego = game_session.run()
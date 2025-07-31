import pygame          # Biblioteca principal para el desarrollo de juegos
import pygame.freetype # Módulo para renderizar fuentes con más control (ej. tamaño)
import random          # Para generar números aleatorios (letras, posición de estrellas)
import math            # Para funciones matemáticas (sin para la animación oscilante)
import time            # Para medir el tiempo (duración de la intro, animaciones)
import json            # Para guardar y cargar la configuración del juego en un archivo JSON
import os              # Para interactuar con el sistema operativo (rutas de archivos)
import sys             # Para controlar el sistema (salir del juego)
from datetime import datetime # Para gestionar las marcas de tiempo de las partidas guardadas

# Importa todas las clases de power-ups y managers
from powerups import PowerUp, ShieldPowerUp, DoubleScorePowerUp
from score_manager import ScoreManager
from keyboard_layout_manager import KeyboardLayoutManager
from game_level_manager import GameLevelManager # ¡NUEVO! Importa GameLevelManager
from render_utils import render_text_gradient  # ¡NUEVO! Importa la función de renderizado de texto

# ========================
# CONFIGURACIÓN INICIAL
# ========================
pygame.init()          # Inicializa todos los módulos de Pygame
pygame.freetype.init() # Inicializa el módulo de fuentes freetype
pygame.mixer.init()    # Asegura que el mezclador de sonido se inicialice temprano
clock = pygame.time.Clock() # Crea un objeto Clock para controlar la velocidad de fotogramas

info = pygame.display.Info() # Obtiene información de la pantalla actual
ANCHO, ALTO = info.current_w, info.current_h # Establece el ancho y alto de la pantalla a la resolución actual
pantalla = pygame.display.set_mode((ANCHO, ALTO)) # Crea la ventana del juego a pantalla completa
pygame.display.set_caption("SpeedType Animated") # Establece el título de la ventana

# ========================
# COLORES Y FUENTES DISPONIBLES
# ========================
NEGRO = (0, 0, 0)       # Definición del color negro (RGB)
BLANCO = (255, 255, 255) # Definición del color blanco (RGB)
ROJO = (255, 0, 0)     # Definición del color rojo (RGB)
VERDE = (0, 255, 0)    # Definición del color verde (RGB)
GRIS_OSCURO = (50, 50, 50) # Nuevo color para el botón
GRIS_CLARO = (100, 100, 100) # Nuevo color para el botón (hover)
AMARILLO = (255, 255, 0)

colores_disponibles = [ # Lista de colores predefinidos para la personalización
    (255, 255, 255),      # Blanco
    (255, 0, 0),          # Rojo
    (0, 255, 0),          # Verde
    (0, 0, 255),          # Azul
    (255, 255, 0),        # Amarillo
    (255, 165, 0),        # Naranja
    (128, 0, 128)         # Púrpura
]

fuentes_disponibles = ["arial", "comicsansms", "couriernew", "verdana"] # Nombres de fuentes del sistema disponibles

# ==================================
# ESTILOS NEÓN PARA TEXTOS DEL MENÚ
# ==================================

# Elige uno de los estilos disponibles
ESTILO_NEON = "fucsia_cian"  # Cambia esta variable para probar otros estilos

estilos_neon = {
    "fucsia_cian": {
        "top": (255, 0, 255),    # Fucsia
        "bottom": (0, 255, 255)  # Cian
    },
    "verde_azul": {
        "top": (57, 255, 20),    # Verde neón
        "bottom": (0, 255, 255)  # Azul celeste
    },
    "rosa_naranja": {
        "top": (255, 20, 147),   # Rosa fuerte
        "bottom": (255, 140, 0)  # Naranja vibrante
    },
    "amarillo_verde": {
        "top": (255, 255, 0),    # Amarillo
        "bottom": (0, 255, 127)  # Verde neón suave
    },
    "blanco_azul": {
        "top": (255, 255, 255),  # Blanco
        "bottom": (0, 128, 255)  # Azul eléctrico
    },
    "color_fondo": {
        "top": (0, 128, 255),  # Azul eléctrico
        "bottom": (255, 0, 255)  # Cian
    },
}

# Aplica el estilo seleccionado
COLOR_GRADIENTE_TOP = estilos_neon[ESTILO_NEON]["top"]
COLOR_GRADIENTE_BOTTOM = estilos_neon[ESTILO_NEON]["bottom"]
COLOR_CONTORNO = (0, 0, 0)  # Contorno negro

# FUENTE_LOGO_STYLE vuelve a ser un nombre de fuente del sistema
FUENTE_LOGO_STYLE = "Impact"

# ========================
# CARGAR FONDO
# ========================
try:
    ruta_fondo = os.path.join(os.path.dirname(__file__), "Fondo2.png")
    fondo_img = pygame.image.load(ruta_fondo).convert()
    fondo_img = pygame.transform.scale(fondo_img, (ANCHO, ALTO))
except Exception as e:
    print(f"Error al cargar Fondo2.png: {e}")
    fondo_img = pygame.Surface((ANCHO, ALTO))
    fondo_img.fill(NEGRO)

try:
    ruta_fondo_pausa = os.path.join(os.path.dirname(__file__), "Fondo2.png")
    fondo_pausa_img = pygame.image.load(ruta_fondo_pausa).convert()
    fondo_pausa_img = pygame.transform.scale(fondo_pausa_img, (ANCHO, ALTO))
except Exception as e:
    print(f"Error al cargar el fondo de pausa: {e}")
    fondo_pausa_img = None


# ========================
# ESTRELLAS ANIMADAS
# ========================
estrellas = [[random.randint(0, ANCHO), random.randint(0, ALTO), random.uniform(0.5, 1.5)] for _ in range(100)]

def dibujar_estrellas(velocidad=1):
    """
    Dibuja estrellas que se mueven hacia abajo y reaparecen en la parte superior.
    """
    for estrella in estrellas:
        estrella[1] += estrella[2] * velocidad
        if estrella[1] > ALTO:
            estrella[0] = random.randint(0, ANCHO)
            estrella[1] = 0
        pygame.draw.circle(pantalla, BLANCO, (int(estrella[0]), int(estrella[1])), 2)

# ========================
# PARTICULAS DE EFECTO
# ========================
particulas = [] # Lista para almacenar partículas

def crear_particulas(x, y, color):
    """Crea un rastro de partículas en la posición dada."""
    for _ in range(10): # Genera 10 partículas
        particulas.append({
            'x': x,
            'y': y,
            'vx': random.uniform(-2, 2), # Velocidad en X
            'vy': random.uniform(-2, 2), # Velocidad en Y
            'radius': random.randint(2, 5), # Tamaño
            'color': color,
            'life': 30 # Duración de vida en fotogramas
        })

def actualizar_y_dibujar_particulas():
    """Actualiza la posición y dibuja las partículas, eliminando las que 'mueren'."""
    global particulas
    particulas_vivas = []
    for p in particulas:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['radius'] -= 0.1 # Se encogen con el tiempo
        p['life'] -= 1 # Reduce la vida

        if p['life'] > 0 and p['radius'] > 0:
            pygame.draw.circle(pantalla, p['color'], (int(p['x']), int(p['y'])), int(p['radius']))
            particulas_vivas.append(p)
    particulas = particulas_vivas

# ========================
# SONIDOS
# ========================
music_loaded = False
acierto_sound = None
fallo_sound = None
game_over_sound = None
powerup_activate_sound = None # Sonido general para la activación de cualquier power-up (powerup.mp3)
shield_hit_sound = None         # Sonido específico cuando el escudo absorbe un golpe
double_score_activate_sound = None # Sonido específico para activar doble puntuación

try:
    acierto_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "acierto.wav"))
    fallo_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "fallo.wav"))
    game_over_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "game_over.wav"))
    pygame.mixer.music.load(os.path.join(os.path.dirname(__file__), "musica_fondo.mp3"))
    pygame.mixer.music.set_volume(0.5)
    music_loaded = True
    # --- Cargar sonidos de power-ups ---
    powerup_activate_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "powerup.mp3"))  
    shield_hit_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "letraescudo.mp3"))  
    double_score_activate_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "doblep.mp3"))    
except Exception as e:
    print(f"Error cargando música de fondo o sonidos: {e}")

# ========================
# CARGA DE IMÁGENES DE POWER-UPS
# ========================
powerup_icons = {}
icon_size = 60  
try:
    powerup_icons["ralentizar"] = pygame.image.load(os.path.join(os.path.dirname(__file__), "caracol.png")).convert_alpha()
    powerup_icons["escudo"] = pygame.image.load(os.path.join(os.path.dirname(__file__), "escudo.png")).convert_alpha()
    powerup_icons["doble_puntuacion"] = pygame.image.load(os.path.join(os.path.dirname(__file__), "dos.png")).convert_alpha()
    
    for key, img in powerup_icons.items():
        powerup_icons[key] = pygame.transform.scale(img, (icon_size, icon_size))
except Exception as e:
    print(f"Error cargando iconos de power-ups: {e}. Asegúrate de que los archivos .png estén en la carpeta correcta.")
    for p_type in ["ralentizar", "escudo", "doble_puntuacion"]:
        powerup_icons[p_type] = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)


# ========================
# GUARDAR Y CARGAR CONFIG
# ========================
def guardar_config(fuente, tam, color):
    config = {"fuente": fuente, "tam": tam, "color": color}
    with open("config.json", "w") as f:
        json.dump(config, f)

def cargar_config():
    if os.path.exists("config.json"):
        try:
            with open("config.json") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
            os.remove("config.json")
            return None
    return None

# ========================
# FUNCIONES DE GUARDAR/CARGAR PARTIDA
# ========================
def guardar_partida(estado_juego, game_mode, timestamp_a_actualizar=None):
    """
    Guarda el estado actual del juego.
    Si se proporciona un timestamp, actualiza esa partida.
    Si no, crea una nueva.
    """
    saved_games = cargar_partida()  

    if timestamp_a_actualizar:
        partida_actualizada = False
        for game in saved_games:
            if game.get("timestamp") == timestamp_a_actualizar:
                game["state"] = estado_juego
                game["timestamp"] = datetime.now().isoformat() # Actualiza el timestamp a la hora de guardar
                partida_actualizada = True
                print(f"Partida '{timestamp_a_actualizar}' actualizada.")
                break
        
        if not partida_actualizada:
            timestamp_a_actualizar = None  

    if not timestamp_a_actualizar:
        new_save = {
            "timestamp": datetime.now().isoformat(),
            "mode": game_mode,
            "state": estado_juego
        }
        saved_games.append(new_save)
        print("Nueva partida guardada.")

    # Asegura que solo se guardan las últimas 5 partidas y se ordenan por fecha
    saved_games.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    saved_games = saved_games[:5]

    try:
        with open("partida_guardada.json", "w") as f:
            json.dump(saved_games, f, indent=4)
    except Exception as e:
        print(f"Error al guardar la partida: {e}")


def cargar_partida():
    """Carga el estado del juego desde un archivo JSON."""
    if os.path.exists("partida_guardada.json"):
        try:
            with open("partida_guardada.json", "r") as f:
                content = f.read()
                if content:
                    loaded_data = json.loads(content)
                    if isinstance(loaded_data, list):
                        # Filtra solo las entradas que son diccionarios y tienen timestamp
                        return [s for s in loaded_data if isinstance(s, dict) and 'timestamp' in s]
                    elif isinstance(loaded_data, dict):
                        # Si es un solo dict (formato antiguo), lo convierte a lista para compatibilidad
                        return [loaded_data] if 'timestamp' in loaded_data else []
                    else:
                        print(f"Advertencia: Contenido inesperado al cargar partida. Tipo: {type(loaded_data)}. Se devuelve lista vacía.")
                        return []
                else:
                    return [] # Archivo vacío
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error al cargar las partidas: {e}")
            # Si el archivo está corrupto o vacío, lo eliminamos para evitar futuros errores
            if os.path.exists("partida_guardada.json"):
                os.remove("partida_guardada.json")
            return []
    return [] # Archivo no existe

def eliminar_partida_guardada(timestamp_a_eliminar):
    """Elimina una partida guardada específica del archivo JSON."""
    saved_games = cargar_partida()
    juegos_restantes = [game for game in saved_games if game.get("timestamp") != timestamp_a_eliminar]
    
    try:
        with open("partida_guardada.json", "w") as f:
            json.dump(juegos_restantes, f, indent=4)
    except Exception as e:
        print(f"Error al eliminar la partida: {e}")

# --- INICIO: CÓDIGO AGREGADO PARA PUNTUACIONES ---
def cargar_highscores():
    """Carga las puntuaciones más altas desde un archivo JSON."""
    if not os.path.exists("highscores.json"):
        return []
    try:
        with open("highscores.json", "r") as f:
            scores = json.load(f)
            return sorted(scores, key=lambda x: x['score'], reverse=True)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def guardar_highscores(scores):
    """Guarda la lista de puntuaciones en el archivo JSON."""
    with open("highscores.json", "w") as f:
        json.dump(scores, f, indent=4)

def check_if_highscore(score):
    """Verifica si una puntuación es suficientemente alta para estar en el Top 5."""
    highscores = cargar_highscores()  

    if len(highscores) < 5:
        return True
    
    elif score > highscores[4]['score']:
        return True
        
    return False
# --- FIN: CÓDIGO AGREGADO ---

# ========================
# CLASES DE JUEGO
# ========================
class Button:
    def __init__(self, x, y, width, height, text, font_obj, color, hover_color, text_color=BLANCO, border_color=BLANCO, border_thickness=3, border_radius=10):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font_obj # font_obj ya es una instancia de SysFont con su tamaño
        self.color = color
        self.hover_color = hover_color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.is_hovered = False
        self.border_radius = border_radius
        self.use_logo_style = False  
        self.logo_style_gradient_colors = [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM]
        self.logo_style_border_color = COLOR_CONTORNO
        self.logo_style_border_thickness = 2

    def set_logo_style(self, enable=True, gradient_colors=None, border_color=None, border_thickness=None):
        self.use_logo_style = enable
        if gradient_colors: self.logo_style_gradient_colors = gradient_colors
        if border_color: self.logo_style_border_color = border_color
        if border_thickness: self.logo_style_border_thickness = border_thickness

    def draw(self, surface):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_thickness, border_radius=self.border_radius)

        if self.use_logo_style:
            # Pasa directamente el objeto font a render_text_gradient
            render_text_gradient(self.font, self.text, self.rect, surface,  
                                 self.logo_style_gradient_colors,  
                                 self.logo_style_border_color,  
                                 self.logo_style_border_thickness)
        else:
            text_surface, text_rect = self.font.render(self.text, BLANCO)
            text_rect.center = self.rect.center  
            surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False

# ========================
# PANTALLA INTRODUCCIÓN
# ========================
def pantalla_intro():
    alpha_logo = 0
    fade_in_duration = 1.5
    hold_duration = 1.5
    fade_out_duration = 1.5
    display_duration_total = fade_in_duration + hold_duration + fade_out_duration

    logo_img = None
    try:
        ruta_logo = os.path.join(os.path.dirname(__file__), "Logotipo.png")
        if os.path.exists(ruta_logo):
            logo_img = pygame.image.load(ruta_logo).convert_alpha()
            logo_img = pygame.transform.scale(logo_img, (ANCHO, ALTO))
        else:
            logo_img = None # Si no se encuentra, se establece a None
    except Exception as e:
        print(f"Error al cargar logo.png: {e}")
        logo_img = None

    start_time = time.time()
    
    if music_loaded:
        pygame.mixer.music.play(-1, 0.0)

    while True:
        elapsed_time = time.time() - start_time
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.K_RETURN:
                return

        pantalla.blit(fondo_img, (0, 0))
        
        if elapsed_time < fade_in_duration:
            alpha_logo = int(255 * (elapsed_time / fade_in_duration))
        elif elapsed_time < fade_in_duration + hold_duration:
            alpha_logo = 255
        elif elapsed_time < display_duration_total:
            remaining_time = display_duration_total - elapsed_time
            alpha_logo = int(255 * (remaining_time / fade_out_duration))
        else:
            return

        alpha_logo = max(0, min(255, alpha_logo))

        if logo_img:
            logo_img.set_alpha(alpha_logo)
            pantalla.blit(logo_img, (0, 0))

        pygame.display.flip()
        clock.tick(60)

# ========================
# PANTALLA CONFIGURACIÓN
# ========================
def pantalla_configuracion(config):
    tam = config["tam"] if config else 60
    nombre_fuente = config["fuente"] if config else fuentes_disponibles[0]
    color = tuple(config["color"]) if config else colores_disponibles[0]

    idx_fuente = fuentes_disponibles.index(nombre_fuente) if nombre_fuente in fuentes_disponibles else 0
    idx_color = colores_disponibles.index(color) if color in colores_disponibles else 0

    texto_previo = "A"

    fuente_ui_btns_flecha = pygame.freetype.SysFont("arial", 25)
    fuente_ui_text = pygame.freetype.SysFont("arial", 40)
    fuente_instrucciones = pygame.freetype.SysFont("arial", 25)
    
    fuente_guardar_btn = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 22)
    btn_guardar = Button(ANCHO//2 - 130, ALTO - 100, 260, 60, "GUARDAR Y CONTINUAR", fuente_guardar_btn, GRIS_OSCURO, GRIS_CLARO)  
    btn_guardar.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

    btn_tam_left = Button(ANCHO//2 - 200, 150 + 50, 40, 40, "<", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_tam_right = Button(ANCHO//2 + 160, 150 + 50, 40, 40, ">", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_fuente_left = Button(ANCHO//2 - 200, 150 + 2*50, 40, 40, "<", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_fuente_right = Button(ANCHO//2 + 160, 150 + 2*50, 40, 40, ">", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_color_left = Button(ANCHO//2 - 200, 150 + 3*50, 40, 40, "<", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_color_right = Button(ANCHO//2 + 160, 150 + 3*50, 40, 40, ">", pygame.freetype.SysFont("arial", 25), GRIS_OSCURO, GRIS_CLARO, border_radius=5)

    start_time = time.time()

    while True:
        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas()

        fuente_letras = pygame.freetype.SysFont(nombre_fuente, tam)
        tiempo_actual = time.time() - start_time
        desplazamiento_y = int(10 * math.sin(tiempo_actual * 2))
        y_base = 100
        separacion = 50

        fuente_config_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
        config_titulo_rect = pygame.Rect(0, 0, ANCHO, 50)
        config_titulo_rect.center = (ANCHO // 2, y_base)
        render_text_gradient(fuente_config_titulo, "CONFIGURACIÓN DE LETRAS", config_titulo_rect, pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

        texto_tam, _ = fuente_ui_text.render(f"Tamaño: {tam}", BLANCO)
        texto_fuente, _ = fuente_ui_text.render(f"Fuente: {nombre_fuente}", BLANCO)
        texto_color, _ = fuente_ui_text.render(f"Color:", color)
        texto_prev, rect_prev = fuente_letras.render(texto_previo, color)
        pos_x = ANCHO // 2 - rect_prev.width // 2
        pos_y = y_base + 3*separacion + desplazamiento_y + 40

        pantalla.blit(texto_tam, (ANCHO//2 - texto_tam.get_width()//2, y_base + separacion + 30))
        pantalla.blit(texto_fuente, (ANCHO//2 - texto_fuente.get_width()//2, y_base + 2*separacion + 30))
        pantalla.blit(texto_color, (ANCHO//2 - texto_color.get_width()//2, y_base + 3*separacion + 30))
        pantalla.blit(texto_prev, (pos_x, pos_y))

        largo_linea = rect_prev.width
        line_y = pos_y + rect_prev.height + 5
        brillo = int(150 + 105 * (0.5 + 0.5 * math.sin(tiempo_actual * 4)))
        color_linea = (brillo, brillo, brillo)
        pygame.draw.line(pantalla, color_linea, (pos_x, line_y), (pos_x + largo_linea, line_y), 3)

        instrucciones, rect_instr = fuente_instrucciones.render("← → Tamaño | ↑ ↓ Fuente | C/V Color | ENTER para guardar y continuar", BLANCO)
        linea_instrucciones_y = pos_y + rect_prev.height + 60
        pantalla.blit(instrucciones, (ANCHO//2 - instrucciones.get_width()//2, linea_instrucciones_y))

        btn_tam_left.rect.y = y_base + separacion + 30
        btn_tam_right.rect.y = y_base + separacion + 30
        btn_fuente_left.rect.y = y_base + 2*separacion + 30
        btn_fuente_right.rect.y = y_base + 2*separacion + 30
        btn_color_left.rect.y = y_base + 3*separacion + 30
        btn_color_right.rect.y = y_base + 3*separacion + 30

        btn_tam_left.draw(pantalla)
        btn_tam_right.draw(pantalla)
        btn_fuente_left.draw(pantalla)
        btn_fuente_right.draw(pantalla)
        btn_color_left.draw(pantalla)
        btn_color_right.draw(pantalla)
        btn_guardar.draw(pantalla)

        pygame.display.flip()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if btn_tam_left.handle_event(evento):
                tam = max(30, tam - 5)
            elif btn_tam_right.handle_event(evento):
                tam = min(200, tam + 5)
            elif btn_fuente_left.handle_event(evento):
                idx_fuente = (idx_fuente - 1) % len(fuentes_disponibles)
                nombre_fuente = fuentes_disponibles[idx_fuente]
            elif btn_fuente_right.handle_event(evento):
                idx_fuente = (idx_fuente + 1) % len(fuentes_disponibles)
                nombre_fuente = fuentes_disponibles[idx_fuente]
            elif btn_color_left.handle_event(evento):
                idx_color = (idx_color + 1) % len(colores_disponibles)
                color = colores_disponibles[idx_color]
            elif btn_color_right.handle_event(evento):
                idx_color = (idx_color - 1) % len(colores_disponibles)
                color = colores_disponibles[idx_color]
            elif btn_guardar.handle_event(evento):
                guardar_config(nombre_fuente, tam, color)
                return nombre_fuente, tam, color

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_LEFT: tam = max(30, tam - 5)
                elif evento.key == pygame.K_RIGHT: tam = min(200, tam + 5)
                elif evento.key == pygame.K_DOWN:
                    idx_fuente = (idx_fuente + 1) % len(fuentes_disponibles)
                    nombre_fuente = fuentes_disponibles[idx_fuente]
                elif evento.key == pygame.K_UP:
                    idx_fuente = (idx_fuente - 1) % len(fuentes_disponibles)
                    nombre_fuente = fuentes_disponibles[idx_fuente]
                elif evento.key == pygame.K_c:
                    idx_color = (idx_color + 1) % len(colores_disponibles)
                    color = colores_disponibles[idx_color]
                elif evento.key == pygame.K_v:
                    idx_color = (idx_color - 1) % len(colores_disponibles)
                    color = colores_disponibles[idx_color]
                elif evento.key == pygame.K_RETURN:
                    guardar_config(nombre_fuente, tam, color)
                    return nombre_fuente, tam, color

# ========================
# PANTALLA MENÚ PRINCIPAL
# ========================
def pantalla_menu_principal():
    fuente_creditos = pygame.freetype.SysFont("arial", 25)
    fuente_opciones_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)

    logo_img = None
    try:
        ruta_logo = os.path.join(os.path.dirname(__file__), "remove.png")
        if os.path.exists(ruta_logo):
            logo_img = pygame.image.load(ruta_logo).convert_alpha()
            logo_img = pygame.transform.scale(logo_img, (ANCHO, ALTO))
        else:
            logo_img = None # Si no se encuentra, se establece a None
    except Exception as e:
        print(f"Error al cargar remove.png: {e}")
        logo_img = None

    button_width = 280
    button_height = 60
    button_y_start = ALTO // 2 - 50  
    button_spacing = 80

    btn_modos_juego = Button(ANCHO // 2 - button_width//2, button_y_start, button_width, button_height, "MODOS DE JUEGO", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO)
    btn_modos_juego.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

    btn_puntuaciones = Button(ANCHO // 2 - button_width//2, button_y_start + button_spacing, button_width, button_height, "PUNTUACIONES", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO)
    btn_puntuaciones.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

    btn_cargar = Button(ANCHO // 2 - button_width//2, button_y_start + 2 * button_spacing, button_width, button_height, "CARGAR PARTIDA", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO)
    btn_cargar.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

    btn_config = Button(ANCHO // 2 - button_width//2, button_y_start + 3 * button_spacing, button_width, button_height, "CONFIGURACIÓN", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO)
    btn_config.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

    btn_salir = Button(ANCHO // 2 - button_width//2, button_y_start + 4 * button_spacing, button_width, button_height, "SALIR", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO)
    btn_salir.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)


    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if btn_modos_juego.handle_event(evento): return "seleccion_modo"
            if btn_puntuaciones.handle_event(evento): return "highscores"
            if btn_cargar.handle_event(evento): return "cargar_partida"
            if btn_config.handle_event(evento): return "configuracion"
            if btn_salir.handle_event(evento):
                if confirmar_salida(): 
                    pygame.quit()
                    sys.exit()

            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                if confirmar_salida(): 
                    pygame.quit()
                    sys.exit()

        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas(0.5)

        if logo_img:
            logo_width = 500
            scale_factor = logo_width / logo_img.get_width()
            scaled_logo = pygame.transform.smoothscale(logo_img, (int(logo_img.get_width() * scale_factor), int(logo_img.get_height() * scale_factor)))
            logo_rect = scaled_logo.get_rect(center=(ANCHO // 2, ALTO // 4))  
            pantalla.blit(scaled_logo, logo_rect)
        else:
            fuente_titulo_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 80)
            titulo_rect = pygame.Rect(0, 0, ANCHO, 100)  
            titulo_rect.center = (ANCHO // 2, ALTO // 4)
            render_text_gradient(fuente_titulo_estilo, "SPEEDTYPE", titulo_rect, pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 4)
            
        btn_modos_juego.draw(pantalla)
        btn_puntuaciones.draw(pantalla)
        btn_cargar.draw(pantalla)
        btn_config.draw(pantalla)
        btn_salir.draw(pantalla)

        pygame.display.flip()
        clock.tick(60)

# ========================
# PANTALLA SELECCIÓN DE MODO DE JUEGO
# ========================
def pantalla_seleccion_modo_juego():
    fuente_titulo_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 60)
    fuente_opciones_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)

    btn_arcane = Button(ANCHO // 2 - 150, ALTO // 2 - 100, 300, 70, "MODO ARCANE (1P)", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO)
    btn_arcane.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

    btn_versus = Button(ANCHO // 2 - 150, ALTO // 2 - 10, 300, 70, "MODO VERSUS (2P)", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO)
    btn_versus.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

    btn_volver = Button(ANCHO // 2 - 150, ALTO // 2 + 150, 300, 70, "VOLVER", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO)
    btn_volver.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if btn_arcane.handle_event(evento): return "arcane"
            if btn_versus.handle_event(evento): return "versus"
            if btn_volver.handle_event(evento): return "volver_menu"
            
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                return "volver_menu"

        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas(0.5)

        titulo_rect = pygame.Rect(0, 0, ANCHO, 100)
        titulo_rect.center = (ANCHO // 2, ALTO // 4 - 50)
        render_text_gradient(fuente_titulo_estilo, "SELECCIONAR MODO", titulo_rect, pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 4)

        btn_arcane.draw(pantalla)
        btn_versus.draw(pantalla)
        btn_volver.draw(pantalla)

        pygame.display.flip()
        clock.tick(60)

# ========================
# PANTALLA CONFIGURACIÓN VERSUS (Límite de Tiempo)
# ========================
def pantalla_configuracion_versus():
    fuente_titulo_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
    fuente_opciones_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    fuente_tiempo_num = pygame.freetype.SysFont("arial", 60) # Este texto puede quedar en arial

    tiempos_disponibles = [1, 2, 3, 5]
    tiempo_seleccionado_idx = 0

    btn_tiempo_left = Button(ANCHO // 2 - 200, ALTO // 2 - 30, 40, 40, "<", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_tiempo_right = Button(ANCHO // 2 + 160, ALTO // 2 - 30, 40, 40, ">", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_iniciar = Button(ANCHO // 2 - 150, ALTO // 2 + 100, 300, 70, "INICIAR VERSUS", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO)
    btn_iniciar.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

    btn_volver = Button(ANCHO // 2 - 150, ALTO // 2 + 200, 300, 70, "VOLVER", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO)
    btn_volver.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if btn_tiempo_left.handle_event(evento):
                tiempo_seleccionado_idx = (tiempo_seleccionado_idx - 1) % len(tiempos_disponibles)
            if btn_tiempo_right.handle_event(evento):
                tiempo_seleccionado_idx = (tiempo_seleccionado_idx + 1) % len(tiempos_disponibles)
            if btn_iniciar.handle_event(evento):
                return tiempos_disponibles[tiempo_seleccionado_idx]
            if btn_volver.handle_event(evento):
                return "volver_seleccion_modo"
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_LEFT:
                    tiempo_seleccionado_idx = (tiempo_seleccionado_idx - 1) % len(tiempos_disponibles)
                elif evento.key == pygame.K_RIGHT:
                    tiempo_seleccionado_idx = (tiempo_seleccionado_idx + 1) % len(tiempos_disponibles)
                elif evento.key == pygame.K_RETURN:
                    return tiempos_disponibles[tiempo_seleccionado_idx]
                elif evento.key == pygame.K_ESCAPE:
                    return "volver_seleccion_modo"

        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas(0.5)

        titulo_rect = pygame.Rect(0, 0, ANCHO, 100)
        titulo_rect.center = (ANCHO // 2, ALTO // 4 - 50)
        render_text_gradient(fuente_titulo_estilo, "LÍMITE DE TIEMPO", titulo_rect, pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

        tiempo_texto, _ = fuente_tiempo_num.render(f"{tiempos_disponibles[tiempo_seleccionado_idx]} min", BLANCO)
        tiempo_texto_rect = tiempo_texto.get_rect(center=(ANCHO // 2, ALTO // 2 - 10))
        pantalla.blit(tiempo_texto, tiempo_texto_rect)

        btn_tiempo_left.draw(pantalla)
        btn_tiempo_right.draw(pantalla)
        btn_iniciar.draw(pantalla)
        btn_volver.draw(pantalla)

        pygame.display.flip()
        clock.tick(60)

# ========================
# PANTALLA CONFIGURACIÓN ARCANE (Límite de Fallos)
# ========================
def pantalla_configuracion_arcane():
    fuente_titulo_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
    fuente_opciones_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    fuente_fallos_num = pygame.freetype.SysFont("arial", 60) # Este texto puede quedar en arial

    fallos_disponibles = [5, 10, 15, 20]
    fallos_seleccionado_idx = 1

    btn_fallos_left = Button(ANCHO // 2 - 200, ALTO // 2 - 30, 40, 40, "<", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_fallos_right = Button(ANCHO // 2 + 160, ALTO // 2 - 30, 40, 40, ">", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO, border_radius=5)
    btn_iniciar = Button(ANCHO // 2 - 150, ALTO // 2 + 100, 300, 70, "INICIAR ARCANE", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO)
    btn_iniciar.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

    btn_volver = Button(ANCHO // 2 - 150, ALTO // 2 + 200, 300, 70, "VOLVER", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO)
    btn_volver.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if btn_fallos_left.handle_event(evento):
                fallos_seleccionado_idx = (fallos_seleccionado_idx - 1) % len(fallos_disponibles)
            if btn_fallos_right.handle_event(evento):
                fallos_seleccionado_idx = (fallos_seleccionado_idx + 1) % len(fallos_disponibles)
            if btn_iniciar.handle_event(evento):
                return fallos_disponibles[fallos_seleccionado_idx]
            if btn_volver.handle_event(evento):
                return "volver_seleccion_modo"
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_LEFT:
                    fallos_seleccionado_idx = (fallos_seleccionado_idx - 1) % len(fallos_disponibles)
                elif evento.key == pygame.K_RIGHT:
                    fallos_seleccionado_idx = (fallos_seleccionado_idx + 1) % len(fallos_disponibles)
                elif evento.key == pygame.K_RETURN:
                    return fallos_disponibles[fallos_seleccionado_idx]
                elif evento.key == pygame.K_ESCAPE:
                    return "volver_seleccion_modo"

        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas(0.5)

        titulo_rect = pygame.Rect(0, 0, ANCHO, 100)
        titulo_rect.center = (ANCHO // 2, ALTO // 4 - 50)
        render_text_gradient(fuente_titulo_estilo, "LÍMITE DE FALLOS", titulo_rect, pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

        fallos_texto, _ = fuente_fallos_num.render(f"{fallos_disponibles[fallos_seleccionado_idx]} fallos", BLANCO)
        fallos_texto_rect = fallos_texto.get_rect(center=(ANCHO // 2, ALTO // 2 - 10))
        pantalla.blit(fallos_texto, fallos_texto_rect)

        btn_fallos_left.draw(pantalla)
        btn_fallos_right.draw(pantalla)
        btn_iniciar.draw(pantalla)
        btn_volver.draw(pantalla)

        pygame.display.flip()
        clock.tick(60)

# ========================
# PANTALLA PAUSA
# ========================
def pantalla_de_pausa():
    fuente_pausa_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 60)
    fuente_pausa_opciones = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)

    superficie_oscura = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    superficie_oscura.fill((0, 0, 0, 180))

    btn_reanudar = Button(ANCHO // 2 - 150, ALTO // 2 - 100, 300, 70, "REANUDAR", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO)
    btn_reanudar.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

    btn_guardar_salir = Button(ANCHO // 2 - 150, ALTO // 2, 300, 70, "GUARDAR Y SALIR", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO)
    btn_guardar_salir.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

    btn_salir_sin_guardar = Button(ANCHO // 2 - 150, ALTO // 2 + 100, 300, 70, "SALIR SIN GUARDAR", pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30), GRIS_OSCURO, GRIS_CLARO)
    btn_salir_sin_guardar.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

    if music_loaded:
        pygame.mixer.music.pause()

    while True:
        if fondo_pausa_img:
            pantalla.blit(fondo_pausa_img, (0,0))

        pantalla.blit(superficie_oscura, (0, 0))

        titulo_pausa_rect = pygame.Rect(0, 0, ANCHO, 70)
        titulo_pausa_rect.center = (ANCHO // 2, ALTO // 2 - 200)
        render_text_gradient(fuente_pausa_titulo, "PAUSA", titulo_pausa_rect, pantalla, [BLANCO, (200, 200, 200)], COLOR_CONTORNO, 3)

        btn_reanudar.draw(pantalla)
        btn_guardar_salir.draw(pantalla)
        btn_salir_sin_guardar.draw(pantalla)

        pygame.display.flip()
        clock.tick(60)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                if music_loaded: pygame.mixer.music.unpause()
                return "reanudar"

            if btn_reanudar.handle_event(evento):
                if music_loaded: pygame.mixer.music.unpause()
                return "reanudar"
            
            if btn_guardar_salir.handle_event(evento): return "guardar_y_salir"
            if btn_salir_sin_guardar.handle_event(evento): return "salir_sin_guardar"

# ========================
# GAME OVER Y PANTALLA DE RESULTADOS
# ========================
def pantalla_fin_juego(score, aciertos, fallos, num_jugadores, scores_j1=None, scores_j2=None):
    fuente_ui_go_text = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 40)
    fuente_ui_go_stats = pygame.freetype.SysFont("arial", 30)
    fuente_ui_go_btns = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)
    
    if num_jugadores == 1:
        btn_reiniciar = Button(ANCHO // 2 - 150, ALTO // 2 + 80, 140, 60, "REINICIAR", fuente_ui_go_btns, GRIS_OSCURO, GRIS_CLARO)
        btn_reiniciar.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)
        btn_salir_go = Button(ANCHO // 2 + 10, ALTO // 2 + 80, 140, 60, "SALIR", fuente_ui_go_btns, GRIS_OSCURO, GRIS_CLARO)
        btn_salir_go.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if btn_reiniciar.handle_event(evento):
                    return "reiniciar"
                if btn_salir_go.handle_event(evento):
                    return "menu_principal"

            pantalla.blit(fondo_img, (0, 0))
            dibujar_estrellas()

            total_letras_procesadas = aciertos + fallos
            prec = (aciertos / total_letras_procesadas) * 100 if total_letras_procesadas else 0

            t1_rect = pygame.Rect(0, 0, ANCHO, 50)
            t1_rect.center = (ANCHO // 2, 200)
            render_text_gradient(fuente_ui_go_text, "¡GAME OVER!", t1_rect, pantalla, [ROJO, (255, 100, 0)], COLOR_CONTORNO, 3)

            t2_surf, t2_rect = fuente_ui_go_stats.render(f"Puntaje: {score}", BLANCO)
            t3_surf, t3_rect = fuente_ui_go_stats.render(f"Aciertos: {aciertos} Fallos: {fallos} Precisión: {prec:.2f}%", BLANCO)

            pantalla.blit(t2_surf, (ANCHO//2 - t2_surf.get_width()//2, 250))  
            pantalla.blit(t3_surf, (ANCHO//2 - t3_surf.get_width()//2, 300))  
            
            btn_reiniciar.draw(pantalla)
            btn_salir_go.draw(pantalla)

            pygame.display.flip()
            clock.tick(60)

    else: # num_jugadores == 2
        fuente_resultado_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 60)
        fuente_resultado_texto = pygame.freetype.SysFont("arial", 40)
        fuente_botones = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)

        score_j1 = scores_j1
        score_j2 = scores_j2

        if score_j1 > score_j2:
            ganador = "JUGADOR 1"
            color_ganador = VERDE
        elif score_j2 > score_j1:
            ganador = "JUGADOR 2"
            color_ganador = AMARILLO
        else:
            ganador = "EMPATE"
            color_ganador = BLANCO

        btn_reiniciar = Button(ANCHO // 2 - 160, ALTO - 160, 150, 60, "REINICIAR", fuente_botones, GRIS_OSCURO, GRIS_CLARO)
        btn_reiniciar.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)
        btn_menu = Button(ANCHO // 2 + 10, ALTO - 160, 150, 60, "MENÚ", fuente_botones, GRIS_OSCURO, GRIS_CLARO)
        btn_menu.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 2)

        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if btn_reiniciar.handle_event(evento):
                    return "reiniciar"
                if btn_menu.handle_event(evento):
                    return "menu_principal"
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    return "menu_principal"

            pantalla.blit(fondo_img, (0, 0))
            dibujar_estrellas()

            rect_titulo = pygame.Rect(0, 0, ANCHO, 80)
            rect_titulo.center = (ANCHO // 2, 100)
            render_text_gradient(fuente_resultado_titulo, "RESULTADOS FINALES", rect_titulo, pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 4)

            texto_j1 = f"JUGADOR 1: {score_j1} pts"
            texto_j2 = f"JUGADOR 2: {score_j2} pts"
            surf_j1, _ = fuente_resultado_texto.render(texto_j1, VERDE)
            surf_j2, _ = fuente_resultado_texto.render(texto_j2, AMARILLO)  
            pantalla.blit(surf_j1, (ANCHO // 4 - surf_j1.get_width() // 2, 200))
            pantalla.blit(surf_j2, (3 * ANCHO // 4 - surf_j2.get_width() // 2, 200))

            if ganador != "EMPATE":
                pygame.draw.rect(
                    pantalla, color_ganador,
                    pygame.Rect(
                        (ANCHO // 4 if ganador == "JUGADOR 1" else 3 * ANCHO // 4) - 160,
                        190, 320, 60
                    ), 4, border_radius=10
                )

            fuente_ganador = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
            rect_ganador = pygame.Rect(0, 0, ANCHO, 80)
            rect_ganador.center = (ANCHO // 2, 320)
            render_text_gradient(fuente_ganador, f"GANADOR: {ganador}", rect_ganador, pantalla, [color_ganador, BLANCO], COLOR_CONTORNO, 3)

            btn_reiniciar.draw(pantalla)
            btn_menu.draw(pantalla)

            pygame.display.flip()
            clock.tick(60)

# ========================
# FUNCIONES DE UI DEL JUEGO
# ========================
def confirmar_salida():
    if music_loaded and pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()

    caja_ancho, caja_alto = 400, 200
    caja_x = (ANCHO - caja_ancho) // 2
    caja_y = (ALTO - caja_alto) // 2
    caja_rect = pygame.Rect(caja_x, caja_y, caja_ancho, caja_alto)

    mensaje_font = pygame.freetype.SysFont("arial", 25)
    btn_font_confirm = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 20)

    btn_si = Button(caja_x + caja_ancho // 4 - 50, caja_y + caja_alto - 60, 100, 40, "SÍ", btn_font_confirm, GRIS_OSCURO, GRIS_CLARO)
    btn_si.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 1)

    btn_no = Button(caja_x + (3 * caja_ancho) // 4 - 50, caja_y + caja_alto - 60, 100, 40, "NO", btn_font_confirm, GRIS_OSCURO, GRIS_CLARO)
    btn_no.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 1)

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if btn_si.handle_event(evento):
                return True  
            if btn_no.handle_event(evento):
                if music_loaded:
                    pygame.mixer.music.unpause()
                return False  

        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas()
        
        pygame.draw.rect(pantalla, NEGRO, caja_rect, border_radius=15)
        pygame.draw.rect(pantalla, BLANCO, caja_rect, 3, border_radius=15)

        mensaje_texto, _ = mensaje_font.render("¿Estás seguro que quieres salir?", BLANCO)
        pantalla.blit(mensaje_texto, (caja_x + (caja_ancho - mensaje_texto.get_width()) // 2, caja_y + 40))

        btn_si.draw(pantalla)
        btn_no.draw(pantalla)

        pygame.display.flip()
        clock.tick(60)

# ========================
# FUNCIÓN DE CONTEO REGRESIVO
# ========================
def mostrar_conteo_regresivo(segundos, fuente_obj, color):
    superficie_oscura = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    superficie_oscura.fill((0, 0, 0, 180))

    fuente_conteo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 100)

    for i in range(segundos, 0, -1):
        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas(0.5)
        pantalla.blit(superficie_oscura, (0, 0))

        conteo_texto = str(i)
        conteo_rect = pygame.Rect(0, 0, ANCHO, ALTO)
        render_text_gradient(fuente_conteo, conteo_texto, conteo_rect, pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 5)

        pygame.display.flip()
        pygame.time.delay(1000)

# --- INICIO: CÓDIGO AGREGADO PARA PANTALLAS DE PUNTUACIÓN ---
def pantalla_ingresar_nombre(score):
    """Pantalla para que el jugador ingrese sus iniciales para el high score."""
    fuente_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
    fuente_input = pygame.freetype.SysFont("arial", 60)
    fuente_instr = pygame.freetype.SysFont("arial", 25)
    
    nombre_jugador = ""
    input_activo = True

    while input_activo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN and len(nombre_jugador) > 0:
                    highscores = cargar_highscores()
                    highscores.append({"nombre": nombre_jugador.upper(), "score": score})
                    highscores.sort(key=lambda x: x['score'], reverse=True)
                    guardar_highscores(highscores[:5]) # Guardar solo el top 5
                    input_activo = False
                elif evento.key == pygame.K_BACKSPACE:
                    nombre_jugador = nombre_jugador[:-1]
                elif len(nombre_jugador) < 3 and evento.unicode.isalpha():
                    nombre_jugador += evento.unicode.upper()

        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas()

        titulo_rect = pygame.Rect(0, 0, ANCHO, 50)
        titulo_rect.center = (ANCHO // 2, ALTO // 2 - 150)
        render_text_gradient(fuente_titulo, "¡NUEVO RÉCORD!", titulo_rect, pantalla, [AMARILLO, BLANCO], COLOR_CONTORNO, 3)

        instr_surf, instr_rect = fuente_instr.render("Ingresa tus iniciales (3 letras) y presiona ENTER", BLANCO)
        instr_rect.center = (ANCHO // 2, ALTO // 2 - 80)
        pantalla.blit(instr_surf, instr_rect)

        # Caja de texto
        caja_rect = pygame.Rect(ANCHO // 2 - 100, ALTO // 2 - 40, 200, 80)
        pygame.draw.rect(pantalla, GRIS_OSCURO, caja_rect, border_radius=10)
        pygame.draw.rect(pantalla, BLANCO, caja_rect, 3, border_radius=10)

        nombre_surf, nombre_rect = fuente_input.render(nombre_jugador, BLANCO)
        nombre_rect.center = caja_rect.center
        pantalla.blit(nombre_surf, nombre_rect)

        pygame.display.flip()
        clock.tick(60)

def pantalla_highscores():
    """Muestra la tabla de las 5 puntuaciones más altas."""
    fuente_titulo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 60)
    fuente_score = pygame.freetype.SysFont("arial", 40)
    fuente_btn = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30)

    highscores = cargar_highscores()

    btn_volver = Button(ANCHO // 2 - 150, ALTO - 100, 300, 70, "VOLVER", fuente_btn, GRIS_OSCURO, GRIS_CLARO)
    btn_volver.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)
    
    # --- NUEVO BOTÓN: LIMPIAR PUNTUACIONES ---
    btn_limpiar = Button(ANCHO // 2 - 150, ALTO - 180, 300, 70, "LIMPIAR PUNTUACIONES", fuente_btn, ROJO, (200, 0, 0))
    btn_limpiar.set_logo_style(True, [ROJO, (255, 100, 100)], NEGRO, 2)
    # ----------------------------------------

    scores_run = True
    while scores_run:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if btn_volver.handle_event(evento):
                scores_run = False
            # --- Manejo del botón LIMPIAR ---
            if btn_limpiar.handle_event(evento):
                if os.path.exists("highscores.json"):
                    os.remove("highscores.json")
                    highscores = [] # Vacía la lista actual para que se refleje de inmediato
                    print("Puntuaciones eliminadas.")
                else:
                    print("No hay archivo de puntuaciones para eliminar.")
            # --------------------------------
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                scores_run = False

        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas()

        titulo_rect = pygame.Rect(0, 0, ANCHO, 100)
        titulo_rect.center = (ANCHO // 2, 100)
        render_text_gradient(fuente_titulo, "PUNTUACIONES MÁS ALTAS", titulo_rect, pantalla, [AMARILLO, BLANCO], COLOR_CONTORNO, 4)

        if not highscores:
            no_scores_surf, no_scores_rect = fuente_score.render("Aún no hay récords. ¡Sé el primero!", BLANCO)
            no_scores_rect.center = (ANCHO // 2, ALTO // 2)
            pantalla.blit(no_scores_surf, no_scores_rect)
        else:
            y_pos = 200
            for i, entry in enumerate(highscores):
                texto = f"{i+1}. {entry['nombre']} - {entry['score']}"
                score_surf, score_rect = fuente_score.render(texto, BLANCO)
                score_rect.center = (ANCHO // 2, y_pos)
                pantalla.blit(score_surf, score_rect)
                y_pos += 60

        btn_volver.draw(pantalla)
        btn_limpiar.draw(pantalla) # Dibuja el nuevo botón
        pygame.display.flip()
        clock.tick(60)

# ========================
# MODO ARCANE (1 Jugador)
# ========================
def jugar_arcane(nombre_fuente, tam, color):
    print("Iniciando Modo ARCANE (1 Jugador)...")
    fallos_limit = pantalla_configuracion_arcane()
    if fallos_limit == "volver_seleccion_modo": return "volver_seleccion_modo"
    # Pasar initial_game_speed a GameLevelManager, aunque Level 1 ya tiene su velocidad fija.
    return jugar(nombre_fuente, tam, color, num_jugadores=1, initial_game_speed=1.5, count_wrong_key_faults=True, time_limit_seconds=0, fallos_limit=fallos_limit)

# ========================
# MODO VERSUS (2 Jugadores)
# ========================
def jugar_versus(nombre_fuente, tam, color):
    print("Iniciando Modo VERSUS (2 Jugadores)...")
    time_limit_minutes = pantalla_configuracion_versus()
    if time_limit_minutes == "volver_seleccion_modo": return "volver_seleccion_modo"
    time_limit_seconds = time_limit_minutes * 60
    # Pasar initial_game_speed a GameLevelManager, aunque Level 1 ya tiene su velocidad fija.
    return jugar(nombre_fuente, tam, color, num_jugadores=2, initial_game_speed=2.0, count_wrong_key_faults=True, time_limit_seconds=time_limit_seconds, fallos_limit=10)

# ========================
# PANTALLA SELECCIONAR PARTIDA GUARDADA
# ========================
def pantalla_seleccionar_partida(saved_games):
    fuente_titulo_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 50)
    fuente_opciones_estilo = pygame.freetype.SysFont(FUENTE_LOGO_STYLE, 30) 
    fuente_partida_info = pygame.freetype.SysFont("arial", 25) 
    fuente_eliminar_btn = pygame.freetype.SysFont("arial", 30) 

    btns = []
    y_start = ALTO // 4
    spacing = 80

    for i, save in enumerate(saved_games):
        timestamp_dt = datetime.fromisoformat(save['timestamp'])
        display_time = timestamp_dt.strftime("%Y-%m-%d %H:%M")
        mode_display = "Arcane (1P)" if save['mode'] == "arcane" else "Versus (2P)"
        
        btn_text = f"{i+1}. {mode_display} - {display_time}"
        
        load_btn_y = y_start + i * spacing
        load_btn_font = pygame.freetype.SysFont("arial", 25)
        load_btn = Button(ANCHO // 2 - 250, load_btn_y, 500, 60, btn_text, load_btn_font, GRIS_OSCURO, GRIS_CLARO)
        load_btn.set_logo_style(False)  

        delete_btn_x = load_btn.rect.right + 10
        delete_btn_font = pygame.freetype.SysFont("arial", 30)
        delete_btn = Button(delete_btn_x, load_btn_y, 60, 60, "X", delete_btn_font, (150,0,0), (255,0,0))
        delete_btn.set_logo_style(False)  
        btns.append((load_btn, delete_btn, save))

    btn_volver = Button(ANCHO // 2 - 150, ALTO - 100, 300, 70, "VOLVER", fuente_opciones_estilo, GRIS_OSCURO, GRIS_CLARO)
    btn_volver.set_logo_style(True, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 3)

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            for load_btn, delete_btn, save_data in btns:
                if load_btn.handle_event(evento): return save_data
                if delete_btn.handle_event(evento):
                    eliminar_partida_guardada(save_data['timestamp'])
                    return "refresh"  
            
            if btn_volver.handle_event(evento): return "volver_menu"
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE: return "volver_menu"

        pantalla.blit(fondo_img, (0, 0))
        dibujar_estrellas(0.5)

        titulo_rect = pygame.Rect(0, 0, ANCHO, 100)
        titulo_rect.center = (ANCHO // 2, ALTO // 4 - 50)
        render_text_gradient(fuente_titulo_estilo, "CARGAR PARTIDA", titulo_rect, pantalla, [COLOR_GRADIENTE_TOP, COLOR_GRADIENTE_BOTTOM], COLOR_CONTORNO, 4)

        if not saved_games:
            no_saves_text, _ = fuente_partida_info.render("No hay partidas guardadas.", BLANCO)
            no_saves_text_rect = no_saves_text.get_rect(center=(ANCHO // 2, ALTO // 2))
            pantalla.blit(no_saves_text, no_saves_text_rect)
            
        for load_btn, delete_btn, _ in btns:
            load_btn.draw(pantalla)
            delete_btn.draw(pantalla)
            
        btn_volver.draw(pantalla)

        pygame.display.flip()
        clock.tick(60)

# ========================
# EJECUCIÓN PRINCIPAL
# ========================
if __name__ == '__main__':
    pantalla_intro()
    
    config = cargar_config()
    selected_save_data = None  
    if not config:
        config = {"fuente": fuentes_disponibles[0], "tam": 60, "color": colores_disponibles[0]}
    
    nombre_fuente = config["fuente"]
    tam = config["tam"]
    color = tuple(config["color"])

    while True:
        accion = pantalla_menu_principal()
        
        if accion == "seleccion_modo":
            modo_seleccionado = pantalla_seleccion_modo_juego()
            if modo_seleccionado == "arcane":
                resultado_juego = jugar_arcane(nombre_fuente, tam, color)
            elif modo_seleccionado == "versus":
                resultado_juego = jugar_versus(nombre_fuente, tam, color)
            elif modo_seleccionado == "volver_menu": continue

        elif accion == "highscores":
            pantalla_highscores()
            continue

        elif accion == "cargar_partida":
            while True:
                saved_games_list = cargar_partida()
                selected_save_data = pantalla_seleccionar_partida(saved_games_list)

                if selected_save_data == "refresh":  
                    continue  

                if selected_save_data and selected_save_data != "volver_menu":
                    loaded_state = selected_save_data["state"]
                    loaded_mode = selected_save_data["mode"]
                    loaded_fallos_limit = loaded_state.get("fallos_limit", 10)
                    loaded_time_limit_seconds = loaded_state.get("time_limit_seconds", 0)
                    
                    if loaded_mode == "arcane":
                        resultado_juego = jugar(nombre_fuente=nombre_fuente, tam=tam, color=color,  
                                                num_jugadores=1,  
                                                initial_game_speed=loaded_state.get("velocidad", 1.5),  
                                                count_wrong_key_faults=True,  
                                                fallos_limit=loaded_fallos_limit,  
                                                initial_state=loaded_state,
                                                save_timestamp=selected_save_data["timestamp"])
                    elif loaded_mode == "versus":
                        resultado_juego = jugar(nombre_fuente=nombre_fuente, tam=tam, color=color,  
                                                num_jugadores=2,  
                                                initial_game_speed=loaded_state.get("velocidad", 2.0),  
                                                count_wrong_key_faults=True,  
                                                time_limit_seconds=loaded_time_limit_seconds,  
                                                fallos_limit=loaded_fallos_limit,  
                                                initial_state=loaded_state,
                                                save_timestamp=selected_save_data["timestamp"])
                    else:
                        resultado_juego = None  
                    break  
                else:  
                    break

        elif accion == "configuracion":
            nombre_fuente, tam, color = pantalla_configuracion(config)
            config = {"fuente": nombre_fuente, "tam": tam, "color": color}
            
        if 'resultado_juego' in locals() and resultado_juego == "menu_principal":
            if music_loaded and not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
            del resultado_juego  
            continue
        elif 'resultado_juego' in locals() and resultado_juego == "reiniciar":
            if music_loaded and not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
            if selected_save_data and selected_save_data != "volver_menu":
                if selected_save_data['mode'] == "arcane":
                    resultado_juego = jugar_arcane(nombre_fuente, tam, color)
                elif selected_save_data['mode'] == "versus":
                    resultado_juego = jugar_versus(nombre_fuente, tam, color)
            elif 'modo_seleccionado' in locals():
                if modo_seleccionado == "arcane":
                    resultado_juego = jugar_arcane(nombre_fuente, tam, color)
                elif modo_seleccionado == "versus":
                    resultado_juego = jugar_versus(nombre_fuente, tam, color)
            else:
                del resultado_juego
                continue
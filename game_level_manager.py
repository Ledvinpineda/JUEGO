import pygame
import time
import math
import pygame.freetype # Necesario para SysFont

class GameLevelManager:
    """
    Gestiona la lógica de los niveles del juego, incluyendo la velocidad,
    los umbrales de aciertos y la visualización de mensajes de nivel.
    """

    def __init__(self, initial_speed_unused, screen_width, screen_height, # initial_speed_unused: se mantiene por compatibilidad, pero la velocidad del Nivel 1 es fija.
                 logo_font_style, gradient_top_color, gradient_bottom_color, border_color,
                 render_text_gradient_func): 
        
        self.current_level = 1
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.level_message_visible = False
        self.level_message_start_time = 0
        self.level_message_duration = 2.0 # segundos. (Ajustado a 2 segundos para la pausa de letras)

        # Configuración de estilos para el renderizado del mensaje de nivel
        self.logo_font_style = logo_font_style
        self.gradient_top_color = gradient_top_color
        self.gradient_bottom_color = gradient_bottom_color
        self.border_color = border_color
        
        # Almacenar la función de renderizado de texto para usarla internamente
        self._render_text_gradient_func = render_text_gradient_func 

        # Velocidades y umbrales por nivel.
        # Nivel 1 inicia con 2.0, y los siguientes son multiplicadores de esa BASE (2.0).
        self.base_speed_level_1 = 2.0 # Velocidad fija para el Nivel 1.

        self.level_speeds = {
            1: self.base_speed_level_1,      # Nivel 1 empieza con velocidad 2.0
            2: self.base_speed_level_1 * 1.25, # Nivel 2: 25% más rápido (2.0 * 1.25 = 2.5)
            3: self.base_speed_level_1 * 1.5,  # Nivel 3: 50% más rápido (2.0 * 1.5 = 3.0)
            4: self.base_speed_level_1 * 1.75, # Nivel 4: 75% más rápido (2.0 * 1.75 = 3.5)
            5: self.base_speed_level_1 * 2.0,  # Nivel 5: Doble de velocidad (2.0 * 2.0 = 4.0)
            # Puedes añadir más niveles si lo deseas
        }

        self.level_thresholds = {
            1: 0,   # Nivel 1 se activa con 0 aciertos
            2: 30,  # Nivel 2 se activa con 30 aciertos (solicitado)
            3: 80,  # Nivel 3 se activa con 80 aciertos
            4: 150, # Nivel 4 se activa con 150 aciertos
            5: 250, # Nivel 5 se activa con 250 aciertos
            # Añade más umbrales si tienes más niveles
        }

    def update_level(self, total_correct_hits):
        """
        Actualiza el nivel actual basado en el número total de aciertos.
        Retorna True si el nivel cambió, False en caso contrario.
        """
        new_level_candidate = self.current_level 

        # Iterar en orden inverso para asegurar que se asigna el nivel más alto posible
        for level, threshold in sorted(self.level_thresholds.items(), reverse=True):
            if total_correct_hits >= threshold:
                new_level_candidate = level
                break 

        if new_level_candidate > self.current_level:
            self.current_level = new_level_candidate
            self.level_message_visible = True
            self.level_message_start_time = time.time()
            print(f"¡Nivel {self.current_level} alcanzado! Nueva velocidad base: {self.get_current_level_speed():.2f}")
            return True
        return False

    def get_current_level_speed(self):
        """
        Retorna la velocidad base del juego para el nivel actual.
        """
        # Asegura que siempre se retorne una velocidad, usando la velocidad del Nivel 1 como fallback
        return self.level_speeds.get(self.current_level, self.level_speeds[1])

    def draw_level_message(self, surface):
        """
        Dibuja el mensaje de 'NIVEL X' en la pantalla si está visible.
        """
        if self.level_message_visible:
            elapsed_time = time.time() - self.level_message_start_time
            if elapsed_time < self.level_message_duration:
                # Animación de tamaño para el mensaje de nivel (más grande y animado)
                # Tamaño base 80, oscilación de 20.
                font_size_anim = int(80 + 20 * math.sin(time.time() * 6)) 
                font_level = pygame.freetype.SysFont(self.logo_font_style, font_size_anim)
                
                text_rect = pygame.Rect(0, 0, self.screen_width, 100)
                text_rect.center = (self.screen_width // 2, self.screen_height // 2)
                
                # Usamos la función de renderizado de texto con degradado
                self._render_text_gradient_func(font_level, f"NIVEL {self.current_level}", text_rect, surface,
                                                 [self.gradient_top_color, self.gradient_bottom_color],
                                                 self.border_color, 3)
            else:
                self.level_message_visible = False

    def is_level_message_showing(self):
        """
        Retorna True si el mensaje de cambio de nivel está visible, False en caso contrario.
        """
        if self.level_message_visible:
            # Re-verificar si el tiempo ya pasó para actualizar el estado
            if time.time() - self.level_message_start_time >= self.level_message_duration:
                self.level_message_visible = False
                return False
            return True
        return False

    def to_dict(self):
        """Serializa el estado del GameLevelManager a un diccionario."""
        return {
            "current_level": self.current_level,
            "level_message_visible": self.level_message_visible,
            "level_message_start_time": self.level_message_start_time,
            # No guardamos screen_width/height, colores/fuente, ni la función de renderizado
            # ya que son estáticos o se re-inicializan al cargar.
        }

    @classmethod
    def from_dict(cls, data, initial_speed_unused, screen_width, screen_height,
                  logo_font_style, gradient_top_color, gradient_bottom_color, border_color,
                  render_text_gradient_func): 
        """Deserializa el estado de un diccionario a una instancia de GameLevelManager."""
        instance = cls(initial_speed_unused, screen_width, screen_height,
                       logo_font_style, gradient_top_color, gradient_bottom_color, border_color,
                       render_text_gradient_func) 
        instance.current_level = data.get("current_level", 1)
        instance.level_message_visible = data.get("level_message_visible", False)
        instance.level_message_start_time = data.get("level_message_start_time", 0)
        
        # Al cargar, si el mensaje estaba visible y su tiempo ya expiró, lo ocultamos.
        # Esto evita que aparezca un mensaje viejo al cargar una partida.
        if instance.level_message_visible and \
           (time.time() - instance.level_message_start_time >= instance.level_message_duration):
             instance.level_message_visible = False
        return instance
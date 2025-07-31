# game_session.py

import pygame
import pygame.freetype
import random
import math
import time
import sys

# Importar tus clases y funciones existentes
from powerups import PowerUp, ShieldPowerUp
from score_manager import ScoreManager
from keyboard_layout_manager import KeyboardLayoutManager

class GameSession:
    """ Encapsula toda la lógica y el estado de una sesión de juego activa. """
    def __init__(self, main_module, config, game_options, initial_state=None, save_timestamp=None):
        # Referencias al módulo principal para acceder a variables globales y funciones
        self.main = main_module
        self.pantalla = self.main.pantalla
        self.clock = self.main.clock
        
        # Configuración de apariencia y opciones de juego
        self.config = config
        self.game_options = game_options
        self.save_timestamp = save_timestamp
        self.game_mode = "arcane" if self.game_options["num_jugadores"] == 1 else "versus"
        
        # Fuentes
        self.fuente_letras = pygame.freetype.SysFont(self.config["fuente"], self.config["tam"])
        self.fuente_ui = pygame.freetype.SysFont("arial", 30)
        
        # Botón de Pausa
        fuente_btn_pausa = pygame.freetype.SysFont(self.main.FUENTE_LOGO_STYLE, 20)
        self.btn_pausa = self.main.Button(self.main.ANCHO - 120, 10, 110, 40, "PAUSA", fuente_btn_pausa, self.main.GRIS_OSCURO, self.main.GRIS_CLARO)
        self.btn_pausa.set_logo_style(True)
        
        # Inicialización de Managers
        self.powerup_manager = PowerUp()
        self.keyboard_manager = KeyboardLayoutManager()
        self.player_managers = {}

        # Inicialización del estado del juego
        self.jugadores = {}
        self.velocidad = self.game_options["initial_speed"]
        self.nivel_actual = 1
        self.nivel_mostrado = False
        self.tiempo_mostrar_nivel = 0
        self.duracion_mensaje_nivel = 4
        self.run_flag = True

        # Timers
        self.tiempo_inicio_juego = time.time()
        self.tiempo_pausado_total = 0
        self.tiempo_transcurrido_cargado = 0
        
        # Cargar estado si existe
        if initial_state:
            self._load_state(initial_state)
        else:
            self._setup_new_game()
            self.main.mostrar_conteo_regresivo(3, self.fuente_letras, self.config["color"])
            self.tiempo_inicio_juego = time.time() # Reiniciar tiempo después del conteo

    def _setup_new_game(self):
        """Configura una nueva partida desde cero."""
        if self.game_options["num_jugadores"] == 1:
            self.player_managers["J1"] = ScoreManager()
            self.jugadores["J1"] = {
                "letra_actual": self.keyboard_manager.obtener_nueva_letra(player_id="J1", num_jugadores=1),
                "x": random.randint(0, self.main.ANCHO - 50), "y": 0,
                "color": self.config["color"], "anim_offset": random.uniform(0, 2 * math.pi)
            }
        else: # 2 Jugadores
            self.player_managers["J1"] = ScoreManager()
            self.player_managers["J2"] = ScoreManager()
            self.jugadores = {"J1": {"color": self.main.VERDE}, "J2": {"color": self.main.AMARILLO}}
            self.current_turn_player = "J1"
            self.active_letter = self.keyboard_manager.obtener_nueva_letra(player_id="J1", num_jugadores=2)
            self.active_letter_y = 0
            self.active_letter_x = random.randint(self.config["tam"], self.main.ANCHO // 2 - self.config["tam"])
            
    def _load_state(self, state):
        """Carga el estado del juego desde un diccionario."""
        self.velocidad = state.get("velocidad", self.game_options["initial_speed"])
        self.tiempo_transcurrido_cargado = state.get("tiempo_transcurrido", 0)
        self.keyboard_manager = KeyboardLayoutManager.from_dict(state.get("keyboard_layout_manager", {}))
        self.powerup_manager.activos = state.get("power_ups_activos", {})

        # Cargar managers de puntuación
        self.player_managers["J1"] = ScoreManager.from_dict(state.get("score_manager_j1", {}))
        if self.game_options["num_jugadores"] == 2:
            self.player_managers["J2"] = ScoreManager.from_dict(state.get("score_manager_j2", {}))

        # Cargar estado de las letras
        if self.game_options["num_jugadores"] == 1:
            self.jugadores["J1"] = state.get("J1")
        else:
            self.jugadores = {"J1": {"color": self.main.VERDE}, "J2": {"color": self.main.AMARILLO}}
            self.current_turn_player = state.get("current_turn_player", "J1")
            self.active_letter = state.get("active_letter")
            self.active_letter_x = state.get("active_letter_x")
            self.active_letter_y = state.get("active_letter_y")
        
        # Sincronizar estado de doble puntuación
        if self.powerup_manager.esta_activo("doble_puntuacion"):
            for manager in self.player_managers.values():
                manager.activate_double_score()
        
        self.main.mostrar_conteo_regresivo(3, self.fuente_letras, self.config["color"])
        self.tiempo_inicio_juego = time.time()

    def _create_save_state(self):
        """Crea un diccionario con el estado actual para guardarlo."""
        tiempo_actual = time.time()
        tiempo_transcurrido = (tiempo_actual - self.tiempo_inicio_juego - self.tiempo_pausado_total) + self.tiempo_transcurrido_cargado
        
        state = {
            "velocidad": self.velocidad, "tiempo_transcurrido": tiempo_transcurrido,
            "fallos_limit": self.game_options["fallos_limit"],
            "score_manager_j1": self.player_managers["J1"].to_dict(),
            "keyboard_layout_manager": self.keyboard_manager.to_dict(),
            "power_ups_activos": self.powerup_manager.activos
        }
        if self.game_options["num_jugadores"] == 1:
            state["J1"] = self.jugadores["J1"]
        else:
            state.update({
                "score_manager_j2": self.player_managers["J2"].to_dict(),
                "time_limit_seconds": self.game_options["time_limit_seconds"],
                "current_turn_player": self.current_turn_player,
                "active_letter": self.active_letter,
                "active_letter_x": self.active_letter_x,
                "active_letter_y": self.active_letter_y
            })
        return state

    def _handle_pause(self):
        """Gestiona la lógica de la pantalla de pausa."""
        tiempo_inicio_pausa = time.time()
        accion_pausa = self.main.pantalla_de_pausa()
        self.tiempo_pausado_total += time.time() - tiempo_inicio_pausa

        if accion_pausa == "guardar_y_salir":
            estado_actual = self._create_save_state()
            self.main.guardar_partida(estado_actual, self.game_mode, self.save_timestamp)
            self.run_flag = False
            return "menu_principal"
        elif accion_pausa == "salir_sin_guardar":
            self.run_flag = False
            return "menu_principal"
        elif accion_pausa == "reanudar":
            # Recalcular el tiempo de inicio para compensar la pausa
            tiempo_actual = time.time()
            self.tiempo_transcurrido_cargado += (tiempo_actual - self.tiempo_inicio_juego - self.tiempo_pausado_total)
            self.tiempo_inicio_juego = tiempo_actual
            self.tiempo_pausado_total = 0

    def _handle_events(self):
        """Procesa todas las entradas del usuario."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.run_flag = False; return "quit"
            
            if self.btn_pausa.handle_event(evento) or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
                return self._handle_pause()

            if evento.type == pygame.KEYDOWN and pygame.K_a <= evento.key <= pygame.K_z:
                self._handle_keypress(pygame.key.name(evento.key).upper())
        return None

    def _handle_keypress(self, typed_letter):
        """Gestiona la pulsación de una letra."""
        if self.game_options["num_jugadores"] == 1:
            self._handle_keypress_j1(typed_letter)
        else:
            self._handle_keypress_j2(typed_letter)
            
    def _handle_keypress_j1(self, typed_letter):
        """Lógica de pulsación para 1 jugador."""
        j1_manager = self.player_managers["J1"]
        j1_data = self.jugadores["J1"]
        
        if typed_letter == j1_data["letra_actual"]:
            j1_manager.add_score()
            if self.main.acierto_sound: self.main.acierto_sound.play()
            self.main.crear_particulas(j1_data["x"] + 25, j1_data["y"] + 25, j1_data["color"])
            
            # Generar nueva letra
            j1_data["letra_actual"] = self.keyboard_manager.obtener_nueva_letra(player_id="J1", num_jugadores=1)
            j1_data["x"] = random.randint(self.config["tam"], self.main.ANCHO - self.config["tam"])
            j1_data["y"] = 0
            j1_data["anim_offset"] = random.uniform(0, 2 * math.pi)

            # Generar power-up
            if j1_manager.get_aciertos() > 0 and j1_manager.get_aciertos() % 10 == 0 and not self.powerup_manager.activos:
                self._spawn_powerup()
        else: # Fallo
            self._handle_miss(j1_manager)

    def _handle_keypress_j2(self, typed_letter):
        """Lógica de pulsación para 2 jugadores."""
        current_manager = self.player_managers[self.current_turn_player]

        if typed_letter == self.active_letter:
            current_manager.add_score()
            if self.main.acierto_sound: self.main.acierto_sound.play()

            # Generar power-up
            if current_manager.get_aciertos() > 0 and current_manager.get_aciertos() % 10 == 0 and not self.powerup_manager.activos:
                self._spawn_powerup()

            # Cambiar de turno y generar nueva letra
            self.current_turn_player = "J2" if self.current_turn_player == "J1" else "J1"
            self.active_letter = self.keyboard_manager.obtener_nueva_letra(player_id=self.current_turn_player, num_jugadores=2)
            self.active_letter_y = 0
            margen_seguro = self.config["tam"]
            if self.current_turn_player == "J1":
                self.active_letter_x = random.randint(margen_seguro, self.main.ANCHO // 2 - margen_seguro)
            else:
                self.active_letter_x = random.randint(self.main.ANCHO // 2 + margen_seguro, self.main.ANCHO - margen_seguro)
        else: # Fallo
            self._handle_miss(current_manager)
            
    def _handle_miss(self, manager):
        """Maneja un fallo para cualquier jugador."""
        shielded_hit = self.powerup_manager.esta_activo("escudo")
        manager.handle_miss(shielded=shielded_hit)
        if shielded_hit and self.main.shield_hit_sound:
            self.main.shield_hit_sound.play()
        elif not shielded_hit and self.main.fallo_sound:
            self.main.fallo_sound.play()
            
    def _spawn_powerup(self):
        """Activa un power-up aleatorio."""
        powerup_effects = {
            "ralentizar": {"duration": 10, "sound": self.main.powerup_activate_sound, "effect": lambda: setattr(self, 'velocidad', self.velocidad / 2)},
            "escudo": {"duration": 10, "sound": self.main.powerup_activate_sound, "effect": None},
            "doble_puntuacion": {"duration": 5, "sound": self.main.double_score_activate_sound, "effect": lambda: [m.activate_double_score() for m in self.player_managers.values()]}
        }
        
        tipo = random.choice(list(powerup_effects.keys()))
        info = powerup_effects[tipo]
        
        self.powerup_manager.activar(tipo, info["duration"])
        if info["sound"]: info["sound"].play()
        if info["effect"]: info["effect"]()

    def _update_state(self, dt):
        """Actualiza el estado de todos los objetos del juego."""
        tiempo_actual = time.time()
        self.tiempo_transcurrido = (tiempo_actual - self.tiempo_inicio_juego - self.tiempo_pausado_total) + self.tiempo_transcurrido_cargado

        terminados = self.powerup_manager.actualizar()
        for tipo in terminados:
            if tipo == "ralentizar": self.velocidad *= 2
            elif tipo == "doble_puntuacion":
                for manager in self.player_managers.values(): manager.deactivate_double_score()

        total_aciertos = sum(m.get_aciertos() for m in self.player_managers.values())
        nuevo_nivel = self.nivel_actual
        if total_aciertos >= 80: nuevo_nivel = 3
        elif total_aciertos >= 30: nuevo_nivel = 2
        
        if nuevo_nivel != self.nivel_actual:
            self.nivel_actual = nuevo_nivel
            self.nivel_mostrado = True
            self.tiempo_mostrar_nivel = time.time()
        
        if self.nivel_mostrado and (time.time() - self.tiempo_mostrar_nivel > self.duracion_mensaje_nivel):
            self.nivel_mostrado = False
        
        if self.game_options["num_jugadores"] == 1:
            self.jugadores["J1"]["y"] += self.velocidad * 60 * dt
            if self.jugadores["J1"]["y"] > self.main.ALTO:
                self._handle_miss(self.player_managers["J1"])
                self.jugadores["J1"]["letra_actual"] = self.keyboard_manager.obtener_nueva_letra(player_id="J1", num_jugadores=1)
                self.jugadores["J1"]["x"] = random.randint(self.config["tam"], self.main.ANCHO - self.config["tam"])
                self.jugadores["J1"]["y"] = 0
        else:
            self.active_letter_y += self.velocidad * 60 * dt
            if self.active_letter_y > self.main.ALTO:
                self._handle_miss(self.player_managers[self.current_turn_player])
                self.current_turn_player = "J2" if self.current_turn_player == "J1" else "J1"
                self.active_letter = self.keyboard_manager.obtener_nueva_letra(player_id=self.current_turn_player, num_jugadores=2)
                self.active_letter_y = 0
                margen = self.config["tam"]
                if self.current_turn_player == "J1":
                    self.active_letter_x = random.randint(margen, self.main.ANCHO // 2 - margen)
                else:
                    self.active_letter_x = random.randint(self.main.ANCHO // 2 + margen, self.main.ANCHO - margen)
        
        if self.game_options.get("time_limit_seconds", 0) > 0 and self.tiempo_transcurrido >= self.game_options["time_limit_seconds"]:
            self.run_flag = False
        if any(m.get_fallos() >= self.game_options.get("fallos_limit", 999) for m in self.player_managers.values()):
            self.run_flag = False
            
    def _draw_elements(self):
        """Dibuja todos los elementos en la pantalla."""
        self.pantalla.blit(self.main.fondo_img, (0, 0))
        self.main.dibujar_estrellas(1)
        if self.game_options["num_jugadores"] == 2:
            pygame.draw.line(self.pantalla, self.main.BLANCO, (self.main.ANCHO // 2, 0), (self.main.ANCHO // 2, self.main.ALTO), 2)
        
        tiempo_actual = time.time()
        anim_amplitud = 15; anim_frecuencia = 5
        if self.game_options["num_jugadores"] == 1:
            j1_data = self.jugadores["J1"]
            desplazamiento_x = math.sin(tiempo_actual * anim_frecuencia + j1_data["anim_offset"]) * anim_amplitud
            self.fuente_letras.render_to(self.pantalla, (j1_data["x"] + desplazamiento_x, j1_data["y"]), j1_data["letra_actual"], j1_data["color"])
        else:
            desplazamiento_x = math.sin(tiempo_actual * anim_frecuencia) * anim_amplitud
            self.fuente_letras.render_to(self.pantalla, (self.active_letter_x + desplazamiento_x, self.active_letter_y), self.active_letter, self.jugadores[self.current_turn_player]["color"])

        self.main.actualizar_y_dibujar_particulas()
        self._draw_hud()
        self._draw_shield_effect()
        
        if self.nivel_mostrado:
            fuente_nivel = pygame.freetype.SysFont(self.main.FUENTE_LOGO_STYLE, int(60 + 10 * math.sin(tiempo_actual * 6)))
            rect_nivel = pygame.Rect(0, 0, self.main.ANCHO, 100); rect_nivel.center = (self.main.ANCHO // 2, self.main.ALTO // 2)
            self.main.render_text_gradient(fuente_nivel, f"NIVEL {self.nivel_actual}", rect_nivel, self.pantalla, [self.main.AMARILLO, self.main.BLANCO], self.main.COLOR_CONTORNO, 3)

        self.btn_pausa.draw(self.pantalla)
        pygame.display.flip()

    def _draw_hud(self):
        """Dibuja la interfaz de usuario (puntuación, tiempo, etc.)."""
        p1_color = self.config["color"] if self.game_options["num_jugadores"] == 1 else self.jugadores['J1']['color']
        self.fuente_ui.render_to(self.pantalla, (10, 10), f"J1: {self.player_managers['J1'].get_score()} (Fallos: {self.player_managers['J1'].get_fallos()})", p1_color)
        if self.game_options["num_jugadores"] == 2:
            self.fuente_ui.render_to(self.pantalla, (self.main.ANCHO // 2 + 10, 10), f"J2: {self.player_managers['J2'].get_score()} (Fallos: {self.player_managers['J2'].get_fallos()})", self.jugadores['J2']['color'])
            pygame.draw.circle(self.pantalla, self.jugadores[self.current_turn_player]['color'], (self.main.ANCHO // 4 if self.current_turn_player == 'J1' else 3 * self.main.ANCHO // 4, 50), 10)
        
        if self.game_options["time_limit_seconds"] > 0:
            tiempo_restante = max(0, self.game_options["time_limit_seconds"] - int(self.tiempo_transcurrido))
            minutos, segundos = divmod(int(tiempo_restante), 60)
            self.fuente_ui.render_to(self.pantalla, (self.main.ANCHO // 2 - 70, 50), f"Tiempo: {minutos:02d}:{segundos:02d}", self.main.BLANCO)
        
        if self.game_options["num_jugadores"] == 1 and self.player_managers["J1"].get_racha() > 1:
            racha = self.player_managers["J1"].get_racha()
            combo_text = f"COMBO x{racha}"
            combo_color = self.main.ROJO if racha >= 20 else self.main.AMARILLO if racha >= 10 else self.main.BLANCO
            fuente_combo = pygame.freetype.SysFont("arial", 40)
            texto_surf, texto_rect = fuente_combo.render(combo_text, combo_color)
            offset_x = random.randint(-2, 2) if racha >= 15 else 0
            offset_y = random.randint(-2, 2) if racha >= 15 else 0
            pos_x = (self.main.ANCHO - texto_rect.width) // 2 + offset_x
            pos_y = 20 + offset_y
            self.pantalla.blit(texto_surf, (pos_x, pos_y))

        y_pu_hud = self.main.ALTO - self.main.icon_size - 50
        x_pu_hud = self.main.ANCHO - self.main.icon_size - 50
        for tipo in self.powerup_manager.activos:
            self.pantalla.blit(self.main.powerup_icons[tipo], (x_pu_hud, y_pu_hud))
            tiempo_restante_pu = int(self.powerup_manager.get_remaining_time(tipo))
            font_time = pygame.freetype.SysFont("arial", 18)
            time_surf, time_rect = font_time.render(f"{tiempo_restante_pu}s", self.main.BLANCO)
            time_rect.midright = (x_pu_hud - 5, y_pu_hud + self.main.icon_size // 2)
            self.pantalla.blit(time_surf, time_rect)
            y_pu_hud -= (self.main.icon_size + 10)

    def _draw_shield_effect(self):
        """Dibuja el efecto de escudo alrededor de la letra activa."""
        if self.game_options["num_jugadores"] == 1:
            letra_texto = self.jugadores["J1"]["letra_actual"]
            letra_rect = self.fuente_letras.get_rect(letra_texto)
            letra_rect.topleft = (self.jugadores["J1"]["x"], self.jugadores["J1"]["y"])
        else:
            letra_texto = self.active_letter
            letra_rect = self.fuente_letras.get_rect(letra_texto)
            letra_rect.topleft = (self.active_letter_x, self.active_letter_y)

        radio_circulo = self.config["tam"] // 2 + 10
        if self.powerup_manager.esta_activo("escudo"):
            alfa = int(100 + 155 * (0.5 + 0.5 * math.sin(time.time() * 8)))
            color_escudo = (20, 200, 255, alfa)
        else:
            color_escudo = (50, 50, 50, 50)
        
        shield_surf = pygame.Surface((radio_circulo * 2, radio_circulo * 2), pygame.SRCALPHA)
        pygame.draw.circle(shield_surf, color_escudo, (radio_circulo, radio_circulo), radio_circulo, 3)
        self.pantalla.blit(shield_surf, shield_surf.get_rect(center=letra_rect.center))

    def run(self):
        """Inicia y mantiene el bucle principal del juego."""
        if self.main.music_loaded and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1, 0.0)

        while self.run_flag:
            dt = self.clock.tick(60) / 1000.0
            
            resultado_pausa = self._handle_events()
            if resultado_pausa == "quit":
                pygame.quit(); sys.exit()
            if resultado_pausa:
                return resultado_pausa

            self._update_state(dt)
            self._draw_elements()

        # Fin de juego
        if self.main.game_over_sound: self.main.game_over_sound.play()
        if self.main.music_loaded: pygame.mixer.music.stop()
        pygame.time.delay(1000)

        p1_manager = self.player_managers["J1"]
        
        if self.game_options["num_jugadores"] == 1 and self.main.check_if_highscore(p1_manager.get_score()):
            self.main.pantalla_ingresar_nombre(p1_manager.get_score())

        if self.game_options["num_jugadores"] == 1:
            return self.main.pantalla_fin_juego(p1_manager.get_score(), p1_manager.get_aciertos(), p1_manager.get_fallos(), 1)
        else:
            p2_manager = self.player_managers["J2"]
            return self.main.pantalla_fin_juego(0, p1_manager.get_aciertos() + p2_manager.get_aciertos(),
                                               p1_manager.get_fallos() + p2_manager.get_fallos(), 2,
                                               p1_manager.get_score(), p2_manager.get_score())
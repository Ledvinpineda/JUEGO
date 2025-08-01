# game_session.py

import pygame
import pygame.freetype
import random
import math
import time
import sys

from powerups import PowerUp, ShieldPowerUp
from score_manager import ScoreManager
from keyboard_layout_manager import KeyboardLayoutManager

class GameSession:
    """ Encapsula toda la lógica y el estado de una sesión de juego activa. """
    def __init__(self, main_module, config, game_options, initial_state=None, save_timestamp=None):
        # Referencias al módulo principal
        self.main = main_module
        self.pantalla = self.main.pantalla
        self.clock = self.main.clock
        
        # Configuración y Opciones
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
        
        # Managers
        self.powerup_manager = PowerUp()
        self.keyboard_manager = KeyboardLayoutManager()
        self.player_managers = {}

        # Estado del Juego
        self.letras_en_pantalla = []
        self.jugadores = {}
        
        # Lógica de Velocidad y Niveles
        self.level_data = {
            1: {"threshold": 0, "speed": 2.0},
            2: {"threshold": 30, "speed": 2.5},
            3: {"threshold": 80, "speed": 3.0},
            4: {"threshold": 150, "speed": 3.5}
        }
        self.nivel_actual = 1
        self.velocidad = self.level_data[1]["speed"]
        self.target_speed = 0
        self.hits_since_levelup = 0
        self.hits_for_increment = 0
        
        self.nivel_mostrado = False
        self.tiempo_mostrar_nivel = 0
        self.duracion_mensaje_nivel = 2

        # Timers y Flags
        self.run_flag = True
        self.tiempo_inicio_juego = time.time()
        self.tiempo_pausado_total = 0
        self.tiempo_transcurrido_cargado = 0
        
        if initial_state:
            self._load_state(initial_state)
        else:
            self._setup_new_game()
            self.main.mostrar_conteo_regresivo(3, self.fuente_letras, self.config["color"])
            self.tiempo_inicio_juego = time.time()
        
        self._calculate_gradual_speed_steps()

    def _calculate_gradual_speed_steps(self):
        next_level = self.nivel_actual + 1
        if next_level not in self.level_data:
            self.hits_for_increment = 0; return

        next_level_info = self.level_data[next_level]
        self.target_speed = next_level_info["speed"]
        
        total_aciertos_actual = sum(m.get_aciertos() for m in self.player_managers.values())
        hits_to_next_level = next_level_info["threshold"] - total_aciertos_actual
        speed_diff = self.target_speed - self.velocidad
        
        if speed_diff <= 0.01:
            self.hits_for_increment = 0; return
            
        increments_needed = round(speed_diff / 0.1)
        if increments_needed > 0 and hits_to_next_level > 0:
            self.hits_for_increment = hits_to_next_level // increments_needed
        else:
            self.hits_for_increment = 0

    def _spawn_new_letters(self, count=1):
        if self.game_options["num_jugadores"] != 1: return
        for _ in range(count):
            char = self.keyboard_manager.obtener_nueva_letra(player_id="J1", num_jugadores=1)
            spawn_type = 'top'
            if self.nivel_actual >= 3:
                spawn_type = random.choice(['top', 'top', 'left', 'right'])

            letra = {'char': char, 'color': self.config["color"], 'anim_offset': random.uniform(0, 2 * math.pi)}
            letra['icon_active'] = True

            icon_surface = None
            if spawn_type == 'left' or spawn_type == 'right':
                letra['icon_type'] = 'icono_lateral'
                icon_surface = self.main.spawner_icons['icono_lateral']
            else:
                letra['icon_type'] = 'avion'
                icon_surface = self.main.spawner_icons['avion']

            if spawn_type == 'left':
                letra.update({
                    'icon_x': -icon_surface.get_width(), 'icon_y': random.randint(50, self.main.ALTO - 150),
                    'icon_vx': self.velocidad * 0.75, 'icon_vy': self.velocidad * 0.1
                })
            elif spawn_type == 'right':
                letra.update({
                    'icon_x': self.main.ANCHO + icon_surface.get_width(), 'icon_y': random.randint(50, self.main.ALTO - 150),
                    'icon_vx': -self.velocidad * 0.75, 'icon_vy': self.velocidad * 0.1
                })
            else:
                letra.update({
                    'icon_x': random.randint(self.config["tam"], self.main.ANCHO - self.config["tam"]), 'icon_y': -icon_surface.get_height(),
                    'icon_vx': 0, 'icon_vy': self.velocidad
                })

            distancia_remolque = 20
            if letra['icon_type'] == 'avion':
                letra['letter_x'] = letra['icon_x']
                letra['letter_y'] = letra['icon_y'] + icon_surface.get_height() / 2 + distancia_remolque
            else:
                letra['letter_y'] = letra['icon_y']
                if letra['icon_vx'] > 0:
                    letra['letter_x'] = letra['icon_x'] + icon_surface.get_width() / 2 + distancia_remolque
                else:
                    letra['letter_x'] = letra['icon_x'] - icon_surface.get_width() / 2 - distancia_remolque
            
            self.letras_en_pantalla.append(letra)

    def _setup_new_game(self):
        if self.game_options["num_jugadores"] == 1:
            self.player_managers["J1"] = ScoreManager()
            self.letras_en_pantalla = []
            self._spawn_new_letters(count=1)
        else:
            self.player_managers["J1"] = ScoreManager(); self.player_managers["J2"] = ScoreManager()
            self.jugadores = {"J1": {"color": self.main.VERDE}, "J2": {"color": self.main.AMARILLO}}
            self.current_turn_player = "J1"
            self.active_letter = self.keyboard_manager.obtener_nueva_letra(player_id="J1", num_jugadores=2)
            self.active_letter_y = 0
            self.active_letter_x = random.randint(self.config["tam"], self.main.ANCHO // 2 - self.config["tam"])
            
    def _load_state(self, state):
        self.velocidad = state.get("velocidad", self.game_options["initial_speed"])
        self.tiempo_transcurrido_cargado = state.get("tiempo_transcurrido", 0)
        self.keyboard_manager = KeyboardLayoutManager.from_dict(state.get("keyboard_layout_manager", {}))
        self.powerup_manager.activos = state.get("power_ups_activos", {})
        self.player_managers["J1"] = ScoreManager.from_dict(state.get("score_manager_j1", {}))
        if self.game_options["num_jugadores"] == 2: self.player_managers["J2"] = ScoreManager.from_dict(state.get("score_manager_j2", {}))
        if self.game_options["num_jugadores"] == 1: self.letras_en_pantalla = state.get("letras_en_pantalla", [])
        else:
            self.jugadores = {"J1": {"color": self.main.VERDE}, "J2": {"color": self.main.AMARILLO}}
            self.current_turn_player = state.get("current_turn_player", "J1")
            self.active_letter = state.get("active_letter"); self.active_letter_x = state.get("active_letter_x"); self.active_letter_y = state.get("active_letter_y")
        if self.powerup_manager.esta_activo("doble_puntuacion"):
            for manager in self.player_managers.values(): manager.activate_double_score()
        self.main.mostrar_conteo_regresivo(3, self.fuente_letras, self.config["color"])
        self.tiempo_inicio_juego = time.time()

    def _create_save_state(self):
        tiempo_transcurrido = (time.time()-self.tiempo_inicio_juego-self.tiempo_pausado_total)+self.tiempo_transcurrido_cargado
        state = {"velocidad": self.velocidad, "tiempo_transcurrido": tiempo_transcurrido,
                 "fallos_limit": self.game_options["fallos_limit"], "score_manager_j1": self.player_managers["J1"].to_dict(),
                 "keyboard_layout_manager": self.keyboard_manager.to_dict(), "power_ups_activos": self.powerup_manager.activos}
        if self.game_options["num_jugadores"] == 1: state["letras_en_pantalla"] = self.letras_en_pantalla
        else: state.update({"score_manager_j2": self.player_managers["J2"].to_dict(), "time_limit_seconds": self.game_options["time_limit_seconds"],
                              "current_turn_player": self.current_turn_player, "active_letter": self.active_letter,
                              "active_letter_x": self.active_letter_x, "active_letter_y": self.active_letter_y})
        return state

    def _handle_pause(self):
        tiempo_inicio_pausa = time.time()
        accion_pausa = self.main.pantalla_de_pausa()
        self.tiempo_pausado_total += time.time() - tiempo_inicio_pausa
        if accion_pausa == "guardar_y_salir":
            self.main.guardar_partida(self._create_save_state(), self.game_mode, self.save_timestamp)
            self.run_flag = False; return "menu_principal"
        elif accion_pausa == "salir_sin_guardar":
            self.run_flag = False; return "menu_principal"
        elif accion_pausa == "reanudar":
            tiempo_actual = time.time(); self.tiempo_transcurrido_cargado += (tiempo_actual - self.tiempo_inicio_juego - self.tiempo_pausado_total)
            self.tiempo_inicio_juego = tiempo_actual; self.tiempo_pausado_total = 0

    def _handle_events(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: self.run_flag = False; return "quit"
            if self.btn_pausa.handle_event(evento) or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE): return self._handle_pause()
            if evento.type == pygame.KEYDOWN and pygame.K_a <= evento.key <= pygame.K_z: self._handle_keypress(pygame.key.name(evento.key).upper())
        return None

    def _handle_keypress(self, typed_letter):
        acierto = False
        if self.game_options["num_jugadores"] == 1: acierto = self._handle_keypress_j1(typed_letter)
        else: acierto = self._handle_keypress_j2(typed_letter)
        if acierto: self._check_gradual_speed_increase()

    def _check_gradual_speed_increase(self):
        self.hits_since_levelup += 1
        if self.hits_for_increment > 0 and self.hits_since_levelup >= self.hits_for_increment:
            if self.velocidad < self.target_speed:
                self.velocidad = min(self.target_speed, self.velocidad + 0.1)
                self.hits_since_levelup = 0
    
    def _handle_keypress_j1(self, typed_letter):
        j1_manager = self.player_managers["J1"]; letra_acertada = None
        for letra in self.letras_en_pantalla:
            if typed_letter == letra['char']: letra_acertada = letra; break
        if letra_acertada:
            j1_manager.add_score(); self.main.acierto_sound.play()
            
            self.main.crear_particulas(letra_acertada["letter_x"], letra_acertada["letter_y"], letra_acertada["color"])
            
            self.letras_en_pantalla.remove(letra_acertada)
            if not self.letras_en_pantalla:
                self._spawn_new_letters(count=2 if self.nivel_actual >= 3 else 1)
            if j1_manager.get_aciertos()%10==0 and not self.powerup_manager.activos: self._spawn_powerup()
            return True
        else: self._handle_miss(j1_manager); return False

    def _handle_keypress_j2(self, typed_letter):
        current_manager = self.player_managers[self.current_turn_player]
        if typed_letter == self.active_letter:
            current_manager.add_score(); self.main.acierto_sound.play()
            if current_manager.get_aciertos()%10==0 and not self.powerup_manager.activos: self._spawn_powerup()
            self.current_turn_player = "J2" if self.current_turn_player == "J1" else "J1"
            self.active_letter = self.keyboard_manager.obtener_nueva_letra(player_id=self.current_turn_player, num_jugadores=2)
            self.active_letter_y = 0; margen = self.config["tam"]
            if self.current_turn_player == "J1": self.active_letter_x = random.randint(margen, self.main.ANCHO//2-margen)
            else: self.active_letter_x = random.randint(self.main.ANCHO//2+margen, self.main.ANCHO-margen)
            return True
        else: self._handle_miss(current_manager); return False

    def _handle_miss(self, manager):
        shielded_hit = self.powerup_manager.esta_activo("escudo")
        manager.handle_miss(shielded=shielded_hit)
        if shielded_hit and self.main.shield_hit_sound: self.main.shield_hit_sound.play()
        elif not shielded_hit and self.main.fallo_sound: self.main.fallo_sound.play()
            
    def _spawn_powerup(self):
        effects = {"ralentizar": {"d": 10, "s": self.main.powerup_activate_sound, "e": lambda: setattr(self, 'velocidad', self.velocidad/2)},
                   "escudo": {"d": 10, "s": self.main.powerup_activate_sound, "e": None},
                   "doble_puntuacion": {"d": 5, "s": self.main.double_score_activate_sound, "e": lambda: [m.activate_double_score() for m in self.player_managers.values()]}}
        tipo = random.choice(list(effects.keys())); info = effects[tipo]
        self.powerup_manager.activar(tipo, info["d"])
        if info["s"]: info["s"].play()
        if info["e"]: info["e"]()

    def _update_state(self, dt):
        tiempo_actual = time.time()
        self.tiempo_transcurrido = (tiempo_actual-self.tiempo_inicio_juego-self.tiempo_pausado_total)+self.tiempo_transcurrido_cargado
        terminados = self.powerup_manager.actualizar()
        for tipo in terminados:
            if tipo == "ralentizar": self.velocidad *= 2
            elif tipo == "doble_puntuacion": [m.deactivate_double_score() for m in self.player_managers.values()]
        
        total_aciertos = sum(m.get_aciertos() for m in self.player_managers.values())
        nuevo_nivel = self.nivel_actual
        for level, data in sorted(self.level_data.items(), reverse=True):
            if total_aciertos >= data["threshold"]: nuevo_nivel = level; break
        if nuevo_nivel != self.nivel_actual:
            self.nivel_actual = nuevo_nivel; self.nivel_mostrado = True
            self.tiempo_mostrar_nivel = time.time(); self.hits_since_levelup = 0
            self._calculate_gradual_speed_steps()
        if self.nivel_mostrado and (time.time()-self.tiempo_mostrar_nivel > self.duracion_mensaje_nivel): self.nivel_mostrado = False
        
        if self.game_options["num_jugadores"] == 1:
            for letra in list(self.letras_en_pantalla):
                letra['icon_x'] += letra['icon_vx'] * 60 * dt
                letra['icon_y'] += letra['icon_vy'] * 60 * dt

                if letra['icon_active']:
                    icon_surface = self.main.spawner_icons[letra['icon_type']]
                    distancia_remolque = 20
                    easing_factor = 0.1
                    
                    target_x, target_y = 0, 0
                    if letra['icon_type'] == 'avion':
                        target_x = letra['icon_x']
                        target_y = letra['icon_y'] + icon_surface.get_height() / 2 + distancia_remolque
                    else:
                        target_y = letra['icon_y']
                        if letra['icon_vx'] > 0:
                            target_x = letra['icon_x'] + icon_surface.get_width() / 2 + distancia_remolque
                        else:
                            target_x = letra['icon_x'] - icon_surface.get_width() / 2 - distancia_remolque
                    
                    letra['letter_x'] += (target_x - letra['letter_x']) * easing_factor
                    letra['letter_y'] += (target_y - letra['letter_y']) * easing_factor
                
                if (letra['icon_y'] > self.main.ALTO + 50 or letra['icon_x'] > self.main.ANCHO + 100 or letra['icon_x'] < -100):
                    self._handle_miss(self.player_managers["J1"])
                    self.letras_en_pantalla.remove(letra)
                    if not self.letras_en_pantalla:
                        self._spawn_new_letters(count=2 if self.nivel_actual >= 3 else 1)
        else:
            self.active_letter_y += self.velocidad * 60 * dt
            if self.active_letter_y > self.main.ALTO:
                self._handle_miss(self.player_managers[self.current_turn_player])
                self.current_turn_player = "J2" if self.current_turn_player == "J1" else "J1"
                self.active_letter = self.keyboard_manager.obtener_nueva_letra(player_id=self.current_turn_player, num_jugadores=2)
                self.active_letter_y = 0; margen = self.config["tam"]
                if self.current_turn_player == "J1": self.active_letter_x = random.randint(margen, self.main.ANCHO//2-margen)
                else: self.active_letter_x = random.randint(self.main.ANCHO//2+margen, self.main.ANCHO-margen)
        
        if self.game_options.get("time_limit_seconds",0)>0 and self.tiempo_transcurrido >= self.game_options["time_limit_seconds"]: self.run_flag=False
        if any(m.get_fallos() >= self.game_options.get("fallos_limit",999) for m in self.player_managers.values()): self.run_flag=False
            
    def _draw_elements(self):
        self.pantalla.blit(self.main.fondo_img, (0, 0)); self.main.dibujar_estrellas(1)
        if self.game_options["num_jugadores"] == 2: pygame.draw.line(self.pantalla, self.main.BLANCO, (self.main.ANCHO // 2, 0), (self.main.ANCHO // 2, self.main.ALTO), 2)
        
        tiempo_actual = time.time(); anim_amplitud = 15; anim_frecuencia = 5
        if self.game_options["num_jugadores"] == 1:
            for letra in self.letras_en_pantalla:
                icon_surface = self.main.spawner_icons[letra['icon_type']]
                icon_rect = icon_surface.get_rect(center=(letra['icon_x'], letra['icon_y']))
                self.pantalla.blit(icon_surface, icon_rect)

                letra_surf, letra_rect = self.fuente_letras.render(letra["char"], letra["color"])
                letra_rect.center = (letra['letter_x'], letra['letter_y'])
                self.pantalla.blit(letra_surf, letra_rect)

                pygame.draw.line(self.pantalla, self.main.GRIS_CLARO, icon_rect.center, letra_rect.center, 2)

        else:
            desplazamiento_x_sin = math.sin(tiempo_actual * anim_frecuencia) * anim_amplitud
            self.fuente_letras.render_to(self.pantalla, (self.active_letter_x + desplazamiento_x_sin, self.active_letter_y), self.active_letter, self.jugadores[self.current_turn_player]["color"])

        self.main.actualizar_y_dibujar_particulas(); self._draw_hud(); self._draw_shield_effect()
        
        if self.nivel_mostrado:
            fuente_nivel = pygame.freetype.SysFont(self.main.FUENTE_LOGO_STYLE, int(60 + 10 * math.sin(tiempo_actual * 6)))
            rect_nivel = pygame.Rect(0, 0, self.main.ANCHO, 100); rect_nivel.center = (self.main.ANCHO//2, self.main.ALTO//2)
            self.main.render_text_gradient(fuente_nivel, f"NIVEL {self.nivel_actual}", rect_nivel, self.pantalla, [self.main.AMARILLO, self.main.BLANCO], self.main.COLOR_CONTORNO, 3)

        self.btn_pausa.draw(self.pantalla)
        pygame.display.flip()

    def _draw_hud(self):
        p1_color = self.config["color"] if self.game_options["num_jugadores"] == 1 else self.jugadores['J1']['color']
        self.fuente_ui.render_to(self.pantalla, (10, 10), f"J1: {self.player_managers['J1'].get_score()} (Fallos: {self.player_managers['J1'].get_fallos()})", p1_color)
        if self.game_options["num_jugadores"] == 2:
            self.fuente_ui.render_to(self.pantalla, (self.main.ANCHO//2+10, 10), f"J2: {self.player_managers['J2'].get_score()} (Fallos: {self.player_managers['J2'].get_fallos()})", self.jugadores['J2']['color'])
            pygame.draw.circle(self.pantalla, self.jugadores[self.current_turn_player]['color'], (self.main.ANCHO//4 if self.current_turn_player=='J1' else 3*self.main.ANCHO//4, 50), 10)
        
        if self.game_options["time_limit_seconds"] > 0:
            tiempo_restante = max(0, self.game_options["time_limit_seconds"]-int(self.tiempo_transcurrido))
            minutos, segundos = divmod(int(tiempo_restante), 60)
            self.fuente_ui.render_to(self.pantalla, (self.main.ANCHO//2-70, 50), f"Tiempo: {minutos:02d}:{segundos:02d}", self.main.BLANCO)
        
        if self.game_options["num_jugadores"] == 1 and self.player_managers["J1"].get_racha() > 1:
            racha = self.player_managers["J1"].get_racha(); combo_text = f"COMBO x{racha}"
            combo_color = self.main.ROJO if racha>=20 else self.main.AMARILLO if racha>=10 else self.main.BLANCO
            fuente_combo = pygame.freetype.SysFont("arial", 40)
            texto_surf, texto_rect = fuente_combo.render(combo_text, combo_color)
            offset_x = random.randint(-2, 2) if racha>=15 else 0; offset_y = random.randint(-2, 2) if racha>=15 else 0
            pos_x = (self.main.ANCHO - texto_rect.width)//2+offset_x; pos_y = 20+offset_y
            self.pantalla.blit(texto_surf, (pos_x, pos_y))

        y_pu_hud = self.main.ALTO-self.main.icon_size-50; x_pu_hud = self.main.ANCHO-self.main.icon_size-50
        for tipo in self.powerup_manager.activos:
            self.pantalla.blit(self.main.powerup_icons[tipo], (x_pu_hud, y_pu_hud))
            tiempo_restante_pu = int(self.powerup_manager.get_remaining_time(tipo))
            font_time = pygame.freetype.SysFont("arial", 18)
            time_surf, time_rect = font_time.render(f"{tiempo_restante_pu}s", self.main.BLANCO)
            time_rect.midright = (x_pu_hud-5, y_pu_hud+self.main.icon_size//2); self.pantalla.blit(time_surf, time_rect)
            y_pu_hud -= (self.main.icon_size + 10)

    def _draw_shield_effect(self):
        letras_a_proteger = []
        if self.game_options["num_jugadores"] == 1:
            if self.letras_en_pantalla:
                letra_mas_cercana = min(self.letras_en_pantalla, key=lambda l: (self.main.ALTO - l['icon_y']) if l.get('icon_vx', 0) == 0 else (self.main.ANCHO - l['icon_x'] if l.get('icon_vx', 0) > 0 else l['icon_x']))
                letras_a_proteger.append(letra_mas_cercana)
        else:
            letras_a_proteger.append({'char': self.active_letter, 'x': self.active_letter_x, 'y': self.active_letter_y})

        for letra in letras_a_proteger:
            pos_x, pos_y = letra.get('letter_x', letra.get('x')), letra.get('letter_y', letra.get('y'))
            letra_rect = self.fuente_letras.get_rect(letra['char']); letra_rect.center = (pos_x, pos_y)
            radio_circulo = self.config["tam"]//2 + 10
            if self.powerup_manager.esta_activo("escudo"):
                alfa = int(100+155*(0.5+0.5*math.sin(time.time()*8))); color_escudo = (20, 200, 255, alfa)
            else:
                color_escudo = (50, 50, 50, 50)
            shield_surf = pygame.Surface((radio_circulo*2, radio_circulo*2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, color_escudo, (radio_circulo, radio_circulo), radio_circulo, 3)
            self.pantalla.blit(shield_surf, shield_surf.get_rect(center=letra_rect.center))


    def run(self):
        if self.main.music_loaded and not pygame.mixer.music.get_busy(): pygame.mixer.music.play(-1, 0.0)
        while self.run_flag:
            dt = self.clock.tick(60)/1000.0
            resultado_pausa = self._handle_events()
            if resultado_pausa == "quit": pygame.quit(); sys.exit()
            if resultado_pausa: return resultado_pausa
            self._update_state(dt)
            self._draw_elements()

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
            return self.main.pantalla_fin_juego(0, p1_manager.get_aciertos()+p2_manager.get_aciertos(),
                                               p1_manager.get_fallos()+p2_manager.get_fallos(), 2,
                                               p1_manager.get_score(), p2_manager.get_score())
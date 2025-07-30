import time

class PowerUp:
    def __init__(self):
        # 'self.activos' es un diccionario para gestionar múltiples power-ups activos
        # Cada entrada es: {"tipo_powerup": {"tiempo_activado": timestamp, "duracion": segundos}}
        self.activos = {} 
        self.duracion_default = 10 # Duración predeterminada si no se especifica

    def activar(self, tipo, duracion=None):
        """
        Activa un power-up específico. Si ya está activo, reinicia su temporizador.
        :param tipo: La cadena que identifica el power-up (ej. "ralentizar", "escudo", "doble_puntuacion").
        :param duracion: Duración en segundos para este power-up; si es None, usa la duración por defecto.
        """
        if duracion is None:
            duracion = self.duracion_default
            
        self.activos[tipo] = {
            "tiempo_activado": time.time(),
            "duracion": duracion
        }
        # print(f"Power-Up '{tipo}' activado por {duracion} segundos.") # Línea para depuración

    def actualizar(self):
        """ 
        Actualiza el estado de TODOS los power-ups activos.
        Elimina los que han excedido su duración.
        Retorna una lista de los tipos de power-ups que han terminado en este ciclo.
        """
        terminados = []
        # Itera sobre una copia de las claves para poder modificar el diccionario mientras iteras
        for tipo in list(self.activos.keys()):
            info_pu = self.activos[tipo]
            if (time.time() - info_pu["tiempo_activado"]) > info_pu["duracion"]:
                del self.activos[tipo] # Elimina el power-up que ha terminado
                terminados.append(tipo)
                # print(f"Power-Up '{tipo}' agotado por tiempo.") # Línea para depuración
        return terminados

    def esta_activo(self, tipo):
        """ 
        Verifica si un power-up específico está actualmente activo.
        :param tipo: La cadena que identifica el power-up.
        :return: True si está activo, False en caso contrario.
        """
        return tipo in self.activos

    def get_remaining_time(self, tipo):
        """ 
        Retorna el tiempo restante de un power-up específico si está activo.
        :param tipo: La cadena que identifica el power-up.
        :return: Tiempo restante en segundos (entero), o 0 si no está activo.
        """
        if tipo in self.activos:
            info_pu = self.activos[tipo]
            elapsed = time.time() - info_pu["tiempo_activado"]
            remaining = info_pu["duracion"] - elapsed
            return max(0, remaining)
        return 0

    def get_remaining_hits(self):
        """
        Adaptación para la UI del escudo: Retorna 1 si el escudo está activo, o 0 si no.
        (Ya que el escudo ya no tiene un conteo de golpes específico en esta versión).
        """
        return 1 if self.esta_activo("escudo") else 0


# --- CLASE POWER-UP DE ESCUDO (Simplificada) ---
class ShieldPowerUp:
    def __init__(self, duration=10): 
        self.duracion_escudo_por_defecto = duration
        self.tipo = "escudo"

    def absorber_golpe(self):
        """
        Este método es una lógica específica del escudo que el gestor principal usará.
        Siempre retorna True si es llamado (asumiendo que el gestor ya verificó que el escudo está activo).
        """
        return True # Si se llama, se asume que el escudo está activo y absorbe el golpe.


# --- NUEVA CLASE PARA EL POWER-UP DE DOBLE PUNTUACIÓN ---
class DoubleScorePowerUp:
    def __init__(self, duration=5): # Duración por defecto para doble puntuación
        self.duracion_doble_puntuacion_por_defecto = duration
        self.tipo = "doble_puntuacion"
# powerups.py

import time

class PowerUp:
    def __init__(self):
        self.activo = None
        self.tiempo_activado = 0
        self.duracion = 10  # duración en segundos

    def activar(self, tipo):
        self.activo = tipo
        self.tiempo_activado = time.time()

    def actualizar(self):
        """ Verifica si el power-up debe terminar """
        if self.activo and (time.time() - self.tiempo_activado) > self.duracion:
            tipo = self.activo
            self.activo = None
            return tipo  # Informa cuál terminó
        return None

    def esta_activo(self, tipo):
        return self.activo == tipo
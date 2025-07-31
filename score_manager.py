
# score_manager.py

class ScoreManager:
    def __init__(self, is_double_score_active=False):
        self.score = 0
        self.aciertos = 0
        self.fallos = 0
        self.racha_actual = 0
        self.is_double_score_active = is_double_score_active # Estado inicial de doble puntuación

    def add_score(self):
        """Añade puntos al marcador, considerando el power-up de doble puntuación.
        Cada acierto suma 1 punto, o 2 si el power-up de doble puntuación está activo.
        También incrementa el contador de aciertos y la racha actual."""
        points_to_add = 1
        if self.is_double_score_active:
            points_to_add *= 2
        self.score += points_to_add
        self.aciertos += 1
        self.racha_actual += 1
        # Aquí podrías añadir lógica para bonos por racha si decides tenerlos en el futuro
        # Por ejemplo: if self.racha_actual > 0 and self.racha_actual % 10 == 0: self.score += 50

    def handle_miss(self, shielded=False):
        """Maneja un fallo. Reinicia la racha y cuenta el fallo si no está protegido
        por un escudo. No resta puntos del marcador."""
        if not shielded:
            self.fallos += 1
        self.racha_actual = 0 # La racha siempre se rompe con un fallo, incluso si es absorbido

    def activate_double_score(self):
        """Activa el modo de doble puntuación."""
        self.is_double_score_active = True

    def deactivate_double_score(self):
        """Desactiva el modo de doble puntuación."""
        self.is_double_score_active = False

    def get_score(self):
        """Retorna la puntuación actual."""
        return self.score

    def get_aciertos(self):
        """Retorna el número total de aciertos."""
        return self.aciertos

    def get_fallos(self):
        """Retorna el número total de fallos."""
        return self.fallos
    
    def get_racha(self):
        """Retorna la racha de aciertos actual."""
        return self.racha_actual

    def to_dict(self):
        """Serializa el estado del ScoreManager a un diccionario para guardar en JSON."""
        return {
            "score": self.score,
            "aciertos": self.aciertos,
            "fallos": self.fallos,
            "racha_actual": self.racha_actual,
            "is_double_score_active": self.is_double_score_active
        }

    @classmethod
    def from_dict(cls, data):
        """Deserializa un diccionario (desde JSON) para crear una instancia de ScoreManager."""
        manager = cls(is_double_score_active=data.get("is_double_score_active", False))
        manager.score = data.get("score", 0)
        manager.aciertos = data.get("aciertos", 0)
        manager.fallos = data.get("fallos", 0)
        manager.racha_actual = data.get("racha_actual", 0)
        return manager
import random
import json

class KeyboardLayoutManager:
    def __init__(self):
        self.left_hand_keys = [
            'Q', 'W', 'E', 'R', 'T',
            'A', 'S', 'D', 'F', 'G',
            'Z', 'X', 'C', 'V', 'B'
        ]
        self.right_hand_keys = [
            'Y', 'U', 'I', 'O', 'P',
            'H', 'J', 'K', 'L', # Asumiendo un teclado español con 'Ñ'
            'N', 'M'
        ]
        
        self.all_game_letters = list(set(self.left_hand_keys + self.right_hand_keys))
        
        # Estas variables almacenarán el estado actual de las letras disponibles
        # y se inicializarán correctamente con reset_available_letters()
        self.current_available_letters_j1 = []
        self.current_available_letters_j2 = []
        self.current_all_letters = []

        # ¡IMPORTANTE! Llama a reset_available_letters al final del constructor
        # Esto asegura que las listas estén llenas cuando se crea una nueva instancia.
        self.reset_available_letters()

    def reset_available_letters(self):
        """Reinicia el pool de letras disponibles para cada jugador (las baraja)."""
        self.current_available_letters_j1 = list(self.left_hand_keys)
        random.shuffle(self.current_available_letters_j1)
        
        self.current_available_letters_j2 = list(self.right_hand_keys)
        random.shuffle(self.current_available_letters_j2)
        
        self.current_all_letters = list(self.all_game_letters)
        random.shuffle(self.current_all_letters)


    def obtener_nueva_letra(self, player_id=None, num_jugadores=1):
        """
        Devuelve una nueva letra aleatoria según el modo de juego y el jugador.
        En modo 2P, selecciona del alfabeto de la mano correspondiente.
        En modo 1P, selecciona del alfabeto completo.
        """
        if num_jugadores == 2 and player_id:
            if player_id == "J1":
                # Si el pool de J1 se agota, lo recarga y lo baraja de nuevo
                if not self.current_available_letters_j1:
                    self.current_available_letters_j1 = list(self.left_hand_keys)
                    random.shuffle(self.current_available_letters_j1) # Barajar al recargar
                return self.current_available_letters_j1.pop(0)
            elif player_id == "J2":
                # Si el pool de J2 se agota, lo recarga y lo baraja de nuevo
                if not self.current_available_letters_j2:
                    self.current_available_letters_j2 = list(self.right_hand_keys)
                    random.shuffle(self.current_available_letters_j2) # Barajar al recargar
                return self.current_available_letters_j2.pop(0)
            else:
                # Si hay un player_id inválido en modo 2P, por defecto se elige de todas las letras
                if not self.current_all_letters:
                    self.current_all_letters = list(self.all_game_letters)
                    random.shuffle(self.current_all_letters) # Barajar al recargar
                return self.current_all_letters.pop(0)
        else: # num_jugadores == 1 o player_id no especificado
            if not self.current_all_letters:
                self.current_all_letters = list(self.all_game_letters)
                random.shuffle(self.current_all_letters) # Barajar al recargar
            return self.current_all_letters.pop(0)

    def to_dict(self):
        """Convierte el estado del manager a un diccionario para guardar."""
        return {
            "left_hand_keys": self.left_hand_keys, # Conservar la definición base
            "right_hand_keys": self.right_hand_keys, # Conservar la definición base
            "current_available_letters_j1": self.current_available_letters_j1,
            "current_available_letters_j2": self.current_available_letters_j2,
            "current_all_letters": self.current_all_letters
        }

    @classmethod
    def from_dict(cls, data):
        """Crea una instancia del manager desde un diccionario cargado.
        Asegura que las listas de letras estén pobladas si el estado cargado está vacío."""
        manager = cls() # Crea una nueva instancia, que ya llama a __init__ y a reset_available_letters()

        # Sobrescribe las listas con los datos cargados si existen
        manager.left_hand_keys = data.get("left_hand_keys", manager.left_hand_keys)
        manager.right_hand_keys = data.get("right_hand_keys", manager.right_hand_keys)
        manager.current_available_letters_j1 = data.get("current_available_letters_j1", [])
        manager.current_available_letters_j2 = data.get("current_available_letters_j2", [])
        manager.current_all_letters = data.get("current_all_letters", [])
        
        # Re-barajar los pools si están vacíos después de la carga
        # Esto es importante para el caso de iniciar un nuevo juego que se crea con from_dict({})
        # o si un juego cargado guardó un pool vacío.
        if not manager.current_available_letters_j1:
            manager.current_available_letters_j1 = list(manager.left_hand_keys)
            random.shuffle(manager.current_available_letters_j1)
        if not manager.current_available_letters_j2:
            manager.current_available_letters_j2 = list(manager.right_hand_keys)
            random.shuffle(manager.current_available_letters_j2)
        if not manager.current_all_letters:
            manager.current_all_letters = list(manager.all_game_letters)
            random.shuffle(manager.current_all_letters)
            
        return manager
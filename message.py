import re


class Message:
    # Définition des regex
    NUM_PATTERN = re.compile(r"^[0-9]{10}$")  # 10 chiffres exacts
    MSG_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,!?'-]+$")  # Message autorisé

    def __init__(self, num: str, msg: str):
        """Initialise un objet Message avec un numéro et un message."""
        self.num = num
        self.msg = msg

    def is_valid_num(self) -> bool:
        """Vérifie si le numéro est valide."""
        return bool(self.NUM_PATTERN.fullmatch(self.num))

    def is_valid_msg(self) -> bool:
        """Vérifie si le message ne contient pas de caractères interdits."""
        return bool(self.MSG_PATTERN.fullmatch(self.msg))

    def is_valid(self) -> bool:
        """Vérifie si le message complet est valide (numéro et texte)."""
        return self.is_valid_num() and self.is_valid_msg()

    def send(self):
        """Simule l'envoi du message si valide."""
        if not self.is_valid():
            raise ValueError("Le message ou le numéro est invalide.")
        print(f"📤 Envoi du message '{self.msg}' au {self.num}...")

    def to_dict(self) -> dict:
        """Retourne une représentation JSON du message."""
        return {"num": self.num, "msg": self.msg}


# Exemple d'utilisation
if __name__ == "__main__":
    msg = Message("0612345678", "Salut, comment ça va ?")

    if msg.is_valid():
        msg.send()
    else:
        print("❌ Erreur : Numéro ou message invalide.")

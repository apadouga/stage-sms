import datetime
import re

from flask import jsonify
from markupsafe import Markup
from modem import GSMModem  # Importation de la classe GSMModem
from requests.utils import is_valid_cidr


class Message:
    # Définition des regex
    NUM_PATTERN = re.compile(r"^[0-9]{10}$")  # 10 chiffres exacts
    MSG_PATTERN = re.compile(r"^[^@#$%^&*()=\\[\]{}<>|`~\";]+$") # caractères spéciaux non désirés (liste noire)

    def __init__(self, num: str, msg: str):
        """Initialise un objet Message après validation des entrées."""
        if not self.is_valid_num(num):
            raise ValueError(f"Numéro invalide : {num}. Il doit contenir exactement 10 chiffres.")

        if not self.is_valid_msg(msg):
            raise ValueError(f"Message invalide : '{msg}'. Il contient des caractères interdits.")

        self.num = num
        self.msg = msg

    def getnum(self):
        return self.num

    def getmsg(self):
        return self.msg

    @classmethod
    def is_valid_num(cls, num: str) -> bool:
        """Vérifie si un numéro est valide."""
        return bool(cls.NUM_PATTERN.fullmatch(num))

    @classmethod
    def is_valid_msg(cls, msg: str) -> bool:
        """Vérifie si un message ne contient pas de caractères interdits."""
        return bool(cls.MSG_PATTERN.fullmatch(msg))

    def send(self, modem):
        """Simule l'envoi du message si valide."""
        print(f"📤 Envoi du message '{self.msg}' au {self.num}...")
        num33 = "+33" + self.num[1:]

        modem.getEcho()
        modem.sendText(num33, self.msg)

    def to_dict(self) -> dict:
        """Retourne une représentation JSON du message."""
        return {"num": self.num, "msg": self.msg}

class MessageRappelRDV(Message):
    """Message de rappel de rendez-vous, envoyé 1 jour avant la date du RDV."""

    def __init__(self, num: str, msg: str, date_rdv: str, heure_rdv: str, type_rdv: str):
        """
        Initialise un rappel de rendez-vous.
        - date_rdv : format YYYY-MM-DD
        - heure_rdv : format HH:MM
        - type_rdv : description du rendez-vous
        """
        super().__init__(num, msg)

        try:
            self.date_rdv = datetime.datetime.strptime(date_rdv, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date invalide : {date_rdv}. Format attendu : YYYY-MM-DD")

        try:
            self.heure_rdv = datetime.datetime.strptime(heure_rdv, "%H:%M").time()
        except ValueError:
            raise ValueError(f"Heure invalide : {heure_rdv}. Format attendu : HH:MM")

        self.type_rdv = type_rdv

    def get_rappel_date(self) -> datetime.datetime:
        """Retourne la date et heure exacte d'envoi du rappel (1 jour avant)."""
        rappel_date = self.date_rdv - datetime.timedelta(days=1)
        return datetime.datetime.combine(rappel_date, self.heure_rdv)

    def send_rappel_automatique(self, modem):
        """Envoie le rappel 1 jour avant la date du rendez-vous."""
        rappel_datetime = self.get_rappel_date()
        now = datetime.datetime.now()

        if now >= rappel_datetime:
            print(f"📅 [{now.strftime('%Y-%m-%d %H:%M')}] Envoi du rappel pour {self.type_rdv} à {self.num}")
            self.send(modem)
        else:
            attente = (rappel_datetime - now).total_seconds()
            print(f"⏳ Le rappel sera envoyé le {rappel_datetime.strftime('%Y-%m-%d %H:%M')}")
            datetime.time.sleep(attente)
            self.send(modem)

class MessageCode(Message):

    def __init__(self, num: str, msg: str, code: str):
        """
        Initialise un message code d'authentification.
        """
        super().__init__(num, msg)


        self.code = code


# Exemple d'utilisation
if __name__ == "__main__":
    msg = Message("0612345678", "Salut, comment ça va même ?")

    value = '<script>alert("XSS Attack")</script>'
    safe_value = Markup.escape(value)
    print(value)
    print(safe_value)


    if msg.is_valid():
        msg.send()
    else:
        print(msg.is_valid_num())
        print(msg.is_valid_msg())
        print("❌ Erreur : Numéro ou message invalide.")

import re
import flask
from flask import request, jsonify
from modem import GSMModem  # Importation de la classe GSMModem

# Définition des regex
NUM_PATTERN = re.compile(r"^[0-9]{10}$")  # 10 chiffres exacts
MSG_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,!?'-]+$")  # Autorise lettres, chiffres, espaces et ponctuation sécurisée


modem = GSMModem('/dev/ttyUSB0')  # Remplacez COM1 par votre port série

app = flask.Flask(__name__)

@app.route('/index')
def index():
    return f"<h1>Hello World!</h1>"


@app.route('/', methods=['GET', 'POST'])
def message():
    if flask.request.method == 'GET':
        return flask.render_template('send-message-post.html')
    else: # request.method == 'POST'
        num = flask.request.form.get('num')
        msg = flask.request.form.get('msg')

        # Vérification du numéro
        if not NUM_PATTERN.fullmatch(num):
            return flask.render_template('erreur.html', erreur="Numéro invalide. Il doit contenir exactement 10 chiffres.")

        # Vérification du message
        if not MSG_PATTERN.fullmatch(msg):
            return flask.render_template('erreur.html', erreur="Message invalide. Évitez les caractères spéciaux interdits.")

        print(f'Le message: {msg}\nA été envoyer au {num}')
        num33 = "+33" + num[1:]
        modem.sendText(num33, msg)

        return flask.render_template('confirmation.html', num=num, msg=msg)


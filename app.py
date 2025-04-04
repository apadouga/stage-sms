import re
import flask
from flask import render_template_string
from markupsafe import Markup

from modem import GSMModem  # Importation de la classe GSMModem
from message import Message, MessageRappelRDV

# Définition des regex
NUM_PATTERN = re.compile(r"^[0-9]{10}$")  # 10 chiffres exactement
MSG_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,!?çéèê'-]+$")  # Autorise lettres, chiffres, espaces et ponctuation sécurisée


modem = GSMModem('/dev/ttyUSB0')  # Remplacez COM1 par votre port série

app = flask.Flask(__name__)


@app.route('/test')
def index():

    return flask.render_template('test-template.html')


@app.route('/', methods=['GET', 'POST'])
def message():
    if flask.request.method == 'GET':
        return flask.render_template('send-message-post.html')
    else: # request.method == 'POST'
        num = flask.request.form.get('num')
        msg = flask.request.form.get('msg')

        rdv = {
            'Numero' : num,
            'Message' : msg
        }

        try:
            message = Message(num, msg)
            message.send(modem)

            return flask.render_template('confirmation.html', rdv=rdv)
        except ValueError as e:
            return flask.render_template('erreur.html',erreur="Numéro invalide. Il doit contenir exactement 10 chiffres.")

@app.route('/rappel', methods=['GET', 'POST'])
def rappel_rdv():
    if flask.request.method == 'GET':
        return flask.render_template('send-RDV-post.html')  # Formulaire HTML

    else:  # POST
        num = flask.request.form.get('num')
        msg = flask.request.form.get('msg')
        date_rdv = flask.request.form.get('date_rdv')
        heure_rdv = flask.request.form.get('heure_rdv')
        type_rdv = flask.request.form.get('type_rdv')

        rdv = {
            'Numero' : num,
            'Message' : msg,
            'Date' : date_rdv,
            'Heure' : heure_rdv,
            'Type' : type_rdv,
        }


        try:
            # Création du message avec validation
            message_rappel = MessageRappelRDV(num, msg, date_rdv, heure_rdv, type_rdv)
            message_rappel.send_rappel_automatique(modem)

            return flask.render_template('confirmation.html', rdv=rdv)

        except ValueError as e:
            return flask.render_template('erreur.html', erreur=str(e))


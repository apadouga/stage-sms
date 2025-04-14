import logging
import os
import re
from datetime import date

import flask
from flask import jsonify, Flask
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

from modem import GSMModem  # Importation de la classe GSMModem
from message import Message, MessageRappelRDV
from logging.handlers import RotatingFileHandler


# Définition de la clé d'api
API_KEY = "table"

app = flask.Flask(__name__)

# Exemple avec SQLite, simple pour commencer
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import des modèles après l'initialisation de db
from modelsDb import MessageDb, Config, User


# Mises en place de logs
if not os.path.exists('logs'):
    os.mkdir('logs')

log_handler = RotatingFileHandler('logs/api.log', maxBytes=1000000, backupCount=3)
log_handler.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

app.logger.addHandler(log_handler)
app.logger.setLevel(logging.DEBUG)



modem = GSMModem('/dev/ttyUSB0')  # Remplacez COM1 par votre port série


# Définition des regex
NUM_PATTERN = re.compile(r"^[0-9]{10}$")  # 10 chiffres exactement
MSG_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,!?çéèê'-]+$")  # Autorise lettres, chiffres, espaces et ponctuation sécurisée


@app.before_request
def log_request_info():
    app.logger.info(
        f"Requête reçue: {flask.request.method} {flask.request.url} | IP: {flask.request.remote_addr}"
    )

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
        type_rdv = flask.request.form.get('msg_template')
        date_rdv = flask.request.form.get('date_rdv')
        heure_rdv = flask.request.form.get('heure_rdv')
        msg = flask.request.form.get('msg_generated')  # le message complet généré côté client

        rdv = {
            'Numero' : num,
            'Date' : date_rdv,
            'Heure' : heure_rdv,
            'Type' : type_rdv,
            'Message': msg,
        }


        try:
            # Création du message avec validation
            print(rdv)

            message_rappel = MessageRappelRDV(num, msg, date_rdv, heure_rdv, type_rdv)
            message_rappel.send_rappel_automatique(modem)

            return flask.render_template('confirmation.html', rdv=rdv)


        except ValueError as e:
            # return flask.render_template('erreur.html', erreur=str(e))
            return flask.render_template('erreur.html', erreur=rdv)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Erreur non gérée: {str(e)}", exc_info=True)
    return {"error": "Une erreur interne est survenue."}, 500


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = flask.request.headers.get('X-API-KEY')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/receive', methods=['POST'])
@require_api_key
def receive_data():
    if not flask.request.is_json:
        app.logger.warning("Invalid content type. JSON expected")
        return jsonify({'status': 'error', 'errorType': 'Invalid content type. JSON expected.'}), 400

    data = flask.request.get_json()
    app.logger.info(f"Requête reçue: {data}")

    # Vérifie que "type" est présent et valide
    message_type = data.get('type')
    if message_type not in ('code', 'msg'):
        app.logger.warning(f"Missing or invalid type field. type: {message_type}")
        return jsonify({'status': 'error', 'errorType': 'Missing or invalid type field. Must be "code" or "msg".'}), 400

    # Vérifie que le numéro est présent et correct
    num = data.get('num')
    if not num or not re.fullmatch(r'0[1-9]\d{8}', num):
        app.logger.warning(f"Missing or invalid num field. num: {num}")
        return jsonify({'status': 'error', 'errorType': 'Missing or invalid num field. Must be French format like 06XXXXXXXX.'}), 400

    # Construction du message selon le type
    if message_type == 'code':
        code = data.get('confirmation_code')
        if not code or not re.fullmatch(r'\d{6}', code):
            app.logger.warning(f"Missing or invalid code field. confirmation_code: {code}")
            return jsonify({'status': 'error', 'errorType': 'Missing or invalid confirmation_code format. Must be exactly 6 digits.'}), 400

        msg = f"Code d'authentification :\n{code}"

    elif message_type == 'msg':
        msg = data.get('message')
        if not msg:
            app.logger.warning(f"Missing message field.")
            return jsonify({'status': 'error', 'errorType': 'Missing message field'}), 400

    # Envoi du message
    try:
        # message = Message(num, msg)
        # message.send(modem)
        app.logger.info(f"Message evoyer, numero: {num}, message: {msg}")

        dateRDV = data.get('dateRDV') if message_type == 'rdv' else None
        message = MessageDb(
            number = num,
            content = msg,
            type = message_type,
            dateRDV = dateRDV,
        )
        db.session.add(message)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'type': message_type,
            'num': num,
            'message': msg
        }), 200
    except ValueError as e:
        app.logger.warning(f"Error: {str(e)}")
        return jsonify({'status': 'error', 'errorType': str(e)}), 400

@app.route ('/db')
def testDb():
    messages = MessageDb.query.all()
    return jsonify([m.to_dict() for m in messages])


import logging
import os
import re
from datetime import datetime, timedelta

import flask
from flask import jsonify, Flask, session, request, redirect, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

from sqlalchemy import func

from modem import GSMModem  # Importation de la classe GSMModem
from message import Message, MessageRappelRDV
from logging.handlers import RotatingFileHandler
from werkzeug.security import check_password_hash, generate_password_hash


# Définition de la clé d'api
API_KEY = "table"

app = flask.Flask(__name__)

app.secret_key = 'fgbveriuvgbeoirgbveiuvgbfovhubefd'
app.permanent_session_lifetime = timedelta(minutes=30)

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

# Initialisation de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # redirection automatique vers /login si l'utilisateur n'est pas connecté

modem = GSMModem('/dev/ttyUSB0')  # Remplacez COM1 par votre port série


# Définition des regex
NUM_PATTERN = re.compile(r"^[0-9]{10}$")  # 10 chiffres exactement
MSG_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,!?çéèê'-]+$")  # Autorise lettres, chiffres, espaces et ponctuation sécurisée



@app.before_request
def log_request_info():
    app.logger.debug(
        f"Requête reçue: {flask.request.method} {flask.request.url} | IP: {flask.request.remote_addr}"
    )

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # hashed_password = generate_password_hash("toto")
    # new_user = User(username="admin", password_hash=hashed_password)
    # db.session.add(new_user)
    # db.session.commit()
    if flask.request.method == 'POST':
        username = flask.request.form['username']
        password = flask.request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return flask.redirect(flask.url_for('message'))
        else:
            return "Identifiants invalides", 401
    return flask.render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for('login'))


@app.route('/')
@login_required
def accueil():

    return flask.render_template('accueil.html')

@app.route('/msg', methods=['GET', 'POST'])
@login_required
def message():
    if flask.request.method == 'GET':
        return flask.render_template('send-message.html')
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

            messageDb = MessageDb(
                number=num,
                content=msg,
                type="msg",
                dateRDV=None,
            )
            db.session.add(messageDb)
            db.session.commit()

            return flask.render_template('confirmation.html', rdv=rdv)
        except ValueError as e:
            return flask.render_template('erreur.html',erreur="Numéro invalide. Il doit contenir exactement 10 chiffres.")

@app.route('/rappel', methods=['GET', 'POST'])
@login_required
def rappel_rdv():
    if flask.request.method == 'GET':
        return flask.render_template('send-rappel.html')  # Formulaire HTML

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

        app.logger.debug(rdv)


        try:
            # Création du message avec validation
            print(rdv)

            message_rappel = MessageRappelRDV(num, msg, date_rdv, heure_rdv, type_rdv)
            message_rappel.send(modem)

            # Fusionne les deux en une seule chaîne, puis convertis-la en objet datetime
            date_heure_str = f"{date_rdv} {heure_rdv}"  # Ex: '2025-04-20 14:30'
            dateRDV = datetime.strptime(date_heure_str, '%Y-%m-%d %H:%M')

            messageDb = MessageDb(
                number=num,
                content=msg,
                type="rdv",
                dateRDV=dateRDV,
            )
            db.session.add(messageDb)
            db.session.commit()
            return flask.render_template('confirmation.html', rdv=rdv)


        except ValueError as e:
            # return flask.render_template('erreur.html', erreur=str(e))
            return flask.render_template('erreur.html', erreur=rdv)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Erreur non gérée: {str(e)}", exc_info=True)
    return {"error": f"Erreur non gérée: {str(e)}"}, 500


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
        messageDb = MessageDb(
            number = num,
            content = msg,
            type = message_type,
            dateRDV = dateRDV,
        )
        db.session.add(messageDb)
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
@login_required
def testDb():
    messages = MessageDb.query.filter(MessageDb.type == 'code').all()
    return [m.to_dict() for m in messages]


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/styles.css')
def styles():
    return flask.send_from_directory('static', 'styles.css')

@app.route('/historique', methods=['GET', 'POST'])
@login_required
def historique():
    if flask.request.method == 'GET':
        return flask.render_template('historique.html', messages=None)
    else: # request.method == 'POST'
        type = flask.request.form.get('type')

        query =db.session.query(
                func.strftime('%Y-%m-%d %H:%M:%S', MessageDb.timestamp).label('timestamp'),
                MessageDb.number,
                MessageDb.type,
                MessageDb.content
            )


        # Ajout du filtre uniquement si `type_recherche` est défini
        if type:
            query = query.filter(MessageDb.type == type)

        messages = query.order_by(MessageDb.timestamp.desc()).all()


        messages = [{
                'timestamp': m.timestamp,
                'number': m.number,
                'type': m.type,
                'content': m.content
            } for m in messages ]

        app.logger.info(f"messages : {messages}")

        if messages == []:
            messages = [{'id': None, 'number': None, 'content': None, 'type': None, 'timestamp': None, 'dateRDV': None}]

        return flask.render_template('historique.html', messages=messages)
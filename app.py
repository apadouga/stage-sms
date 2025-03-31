import flask
from flask import request
from modem import GSMModem  # Importation de la classe GSMModem

modem = GSMModem('/dev/ttyUSB0')  # Remplacez COM1 par votre port série

app = flask.Flask(__name__)

@app.route('/index')
def index():
    return f"<h1>Hello World!</h1>"


@app.route('/', methods=['GET', 'POST'])
def admin_enseignant():
    if flask.request.method == 'GET':
        return flask.render_template('send-message-post.html')
    else: # request.method == 'POST'
        num = flask.request.form.get('num')
        msg = flask.request.form.get('msg')

        print(f'Le message: {msg}\nA été envoyer au {num}')
        num33 = "+33" + num[1:]
        modem.sendText(num33, msg)

        return flask.render_template('confirmation.html', num=num, msg=msg)


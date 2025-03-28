import flask
from flask import request
from testApi.modem import GSMModem  # Importation de la classe GSMModem

modem = GSMModem('COM5')  # Remplacez COM1 par votre port série

app = flask.Flask(__name__)

@app.route('/')
def index():
    return f"<h1>Hello World!</h1>"

@app.route('/param-get')
def param_get():
    num = flask.request.args.get('num')
    msg = flask.request.args.get('msg')

    print(f'Le message: {msg}\nA été envoyer au {num}')
    num33 = "+33" + num[1:]
    modem.sendText(num33, msg)

    return f'Le message: {msg}<br>A été envoyer au numéro {num}'

@app.route('/test')
def test():
    return flask.render_template('test-param-get.html')


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
    app.run(debug=True, port=5000)

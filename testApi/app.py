import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
    return f"<h1>Hello World!</h1>"

@app.route('/param-get')
def param_get():
    num = flask.request.args.get('num', default="512")
    msg = flask.request.args.get('msg', default="hello")
    print(f'Le message: {msg} :\nA été envoyer au {num}')
    return f'Le message: {msg}<br>A été envoyer au numéro {num}'

@app.route('/test')
def test():
    return flask.render_template('test-param-get.html')


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
    app.run(debug=True, port=5001)
# from blueprints import autocomplete_bp, tables_bp, transactions_bp
from blueprints import transactions_bp, persons_bp
from flask import Flask
# from gevent.pywsgi import WSGIServer

backend = Flask(__name__)

# backend.register_blueprint(autocomplete_bp)
# backend.register_blueprint(tables_bp)
backend.register_blueprint(persons_bp)
backend.register_blueprint(transactions_bp)


@backend.template_filter()
def currency_format(value):
    return f'{value:.2f}'


if __name__ == "__main__":
    backend.run(host='localhost', port=5555, debug=True)
    # http_server = WSGIServer(('localhost', 5555), backend)
    # http_server.serve_forever()

from app import create_app
from gevent.pywsgi import WSGIServer


if __name__ == "__main__":
    backend = create_app()
    backend.secret_key = 'super secret key'
    backend.config['SESSION_TYPE'] = 'filesystem'

    http_server = WSGIServer(('localhost', 5555), backend)
    http_server.serve_forever()

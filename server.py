"""Production WSGI entrypoint."""

import os

from waitress import serve

from app import create_app

if __name__ == "__main__":
    backend = create_app()
    backend.secret_key = os.environ.get('SECRET_KEY', backend.config.get('SECRET_KEY', 'dev-secret-key'))
    backend.config['SESSION_TYPE'] = 'filesystem'

    serve(backend, host='0.0.0.0', port=5555)

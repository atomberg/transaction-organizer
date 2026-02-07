"""Development server entrypoint."""

import os

from app import create_app

if __name__ == "__main__":
    backend = create_app()
    backend.secret_key = os.environ.get('SECRET_KEY', backend.config.get('SECRET_KEY', 'dev-secret-key'))
    backend.config['SESSION_TYPE'] = 'filesystem'

    backend.run(host='localhost', port=5555, debug=True)

from app import create_app
from waitress import serve


if __name__ == "__main__":
    backend = create_app()
    backend.secret_key = 'super secret key'
    backend.config['SESSION_TYPE'] = 'filesystem'

    serve(backend, host='127.0.0.1', port=5555)

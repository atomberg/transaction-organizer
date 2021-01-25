from app import create_app


if __name__ == "__main__":
    backend = create_app()
    backend.secret_key = 'super secret key'
    backend.config['SESSION_TYPE'] = 'filesystem'

    backend.run(host='localhost', port=5555, debug=True)

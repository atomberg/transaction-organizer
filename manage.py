from flask_script import Server, Manager
from app.views import backend

manager = Manager(backend)
manager.add_command("runserver", Server(host="localhost", port=5555))

if __name__ == "__main__":
    manager.run()

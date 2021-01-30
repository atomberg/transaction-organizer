"""."""
import datetime
import shutil
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_filename='config.py'):
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)

    # Backup the database file
    backup_path = app.config['SQLALCHEMY_DATABASE_BACKUP_PATH']
    backup_path.mkdir(exist_ok=True, parents=True)
    backup_path /= (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y_%B.bak")
    if not backup_path.exists():
        shutil.copyfile(app.cofig['SQLALCHEMY_DATABASE_PATH'], backup_path)

    db.init_app(app)

    # Import and register blueprints
    from .blueprints import transactions_bp, persons_bp, reports_bp

    app.register_blueprint(persons_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(reports_bp)
    return app

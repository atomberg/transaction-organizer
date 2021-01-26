import datetime
import shutil
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

backup_path = Path('backups')
backup_path.mkdir(exist_ok=True, parents=True)

backup_path /= (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y_%B.bak")
if not backup_path.exists():
    shutil.copyfile('app/donations.db', backup_path)

engine = create_engine('sqlite:///app/donations.db')
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

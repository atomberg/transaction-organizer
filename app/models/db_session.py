from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('sqlite:///transactions.db')
Session = scoped_session(sessionmaker(bind=engine))

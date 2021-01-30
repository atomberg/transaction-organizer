from pathlib import Path


SQLALCHEMY_DATABASE_PATH = Path(__file__).parent / 'test.db'
SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLALCHEMY_DATABASE_PATH.absolute()}'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_BACKUP_PATH = Path(__file__).parent / 'test_backups'

ORG = '''<h5>Success Absolute People but Perfect Chocolate</h5>
         <p>
             123 Funning Avenue, Perfect TT Z1Y 2X3<br>
             Especially Registration # 123456789 AA 0001
         </p>'''
TREASURER = 'Bob Smith'
TAX_YEAR = 2019

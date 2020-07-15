import os

basedir = os.path.dirname(__file__)
basedir = os.path.abspath(basedir)
SQLALCHEMY_TRACK_MODIFICATIONS = False
# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '..', 'sf.db')  # sqlite
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:passwd@localhost/stuff_finder'  # postgres
SECRET_KEY = 'iyvuiYV*V*v8yv8iYV*(7g0bh09'
ITEMS_PER_PAGE = 20

MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
ADMINS = ['3410914@gmail.com']
SECURITY_EMAIL_SENDER = 'valid_email@my_domain.com'

PROXIES = {'https': 'https://hYTwcY:zvRj7H@193.42.125.20:8000'}



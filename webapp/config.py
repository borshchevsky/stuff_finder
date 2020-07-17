import os

basedir = os.path.dirname(__file__)
basedir = os.path.abspath(basedir)
SQLALCHEMY_TRACK_MODIFICATIONS = False
# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '..', 'sf.db')  # sqlite
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:123@localhost/stuff_finder'  # postgres
SECRET_KEY = 'iyvuiYV*V*v8yv8iYV*(7g0bh09'
ITEMS_PER_PAGE = 20

MAIL_SERVER = 'smtp.mail.ru'
MAIL_USERNAME = 'admin@rattle.one'
MAIL_PASSWORD = 'passwd'

SENDER = 'admin@rattle.one'
SUBJ_FOR_EMAIL = 'Цена снизилась!'

PROXIES = {'https': 'https://hYTwcY:zvRj7H@193.42.125.20:8000'}

MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True


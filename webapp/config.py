import os

basedir = os.path.dirname(__file__)
basedir = os.path.abspath(basedir)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '..', 'sf.db')
SECRET_KEY = 'iyvuiYV*V*v8yv8iYV*(7g0bh09'
ITEMS_PER_PAGE = 20

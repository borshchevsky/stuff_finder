from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_migrate import Migrate

from models import db, User, Phone
from webapp.main.views import blueprint as main_blueprint
from webapp.user.views import blueprint as user_blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    db.init_app(app)
    migrate = Migrate(app, db)
    login = LoginManager(app)
    login.login_view = 'user.login'
    login.login_message = 'Для доступа к этой странице необходимо войти на сайт.'
    login.login_message_category = 'danger'

    app.register_blueprint(main_blueprint)
    app.register_blueprint(user_blueprint)

    @login.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'User': User, 'Phone': Phone}

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app


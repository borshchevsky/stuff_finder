from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse

from models import db, User, user_phone, Phone
from webapp.user.forms import LoginForm, RegistrationForm

blueprint = Blueprint('user', __name__)


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not (user and user.check_password(form.password.data)):
            flash('Неверное имя или пароль.', category='danger')
            return redirect(url_for('user.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        flash('Вы успешно вошли на сайт', category='success')
        return redirect(next_page)
    return render_template('user/login.html', form=form, title='Вход')


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрировались!', category='success')
        return redirect(url_for('user.login'))
    return render_template('user/register.html', title='Регистрация', form=form)


@blueprint.route('/favorites', methods=['GET', 'POST'])
def favorites():
    if not current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user_id = User.query.filter_by(username=current_user.username).first().id
    phone_id = request.args.get('phone_id')
    action = request.args.get('action')
    if Phone.query.filter_by(id=phone_id).count():
        if action == 'del':
            if db.session.query(user_phone).filter_by(phone_id=phone_id, user_id=user_id).count():
                db.engine.execute(f'DELETE FROM user_phone WHERE user_id = {user_id} AND phone_id = {phone_id}')
            return redirect(url_for('user.favorites'))
        elif action == 'add':
            result = db.engine.execute(f'SELECT user_id, phone_id FROM user_phone WHERE user_id = {user_id} AND phone_id = {phone_id}')
            if len(list(result)) == 0:
                db.engine.execute(f'INSERT INTO user_phone VALUES ({user_id}, {phone_id})')
                flash('Добавлено в избранные.', category='primary')
            else:
                flash('Этот товар уже в избранных.', category='danger')
            return redirect(url_for('main.index'))
    user_phone_queries = db.session.query(user_phone).filter_by(user_id=user_id).all()
    phone_ids = [phone_id for _, phone_id in user_phone_queries]
    phones = [Phone.query.filter_by(id=phone_id).first() for phone_id in phone_ids]
    return render_template('user/favorites.html', title='Избранное', phones=phones)



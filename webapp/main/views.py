from flask import Blueprint, current_app, render_template, request

from models import Phone

from webapp.user.forms import SpecsForm

blueprint = Blueprint('main', __name__)


@blueprint.route('/')
@blueprint.route('/index')
def index():
    title = 'Stuff Finder'
    phones = Phone.query.all()
    return render_template('main/index.html', page_title=title, phones=phones)


@blueprint.route('/specs')
def show_specs():
    form = SpecsForm()
    phone_id = request.args.get('phone_id', None)
    phone = Phone.query.filter_by(id=phone_id).first()
    return render_template('main/specs.html', form=form, phone=phone)

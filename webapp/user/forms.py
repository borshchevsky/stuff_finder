from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class SearchForm(FlaskForm):
    search = StringField('', render_kw={'class': 'form-control mr-sm-2', 'type': 'search', 'placeholder': 'Поиск',
                                        'aria-label': 'Search', 'style': "width:400px;"})
    search_button = SubmitField('Найти', render_kw={'class': "btn btn-outline-success my-2 my-sm-0", 'type': "submit", 'method': 'post'})

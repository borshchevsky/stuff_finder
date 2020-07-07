from flask import Blueprint, current_app, render_template, request
from fuzzywuzzy import fuzz

from models import Phone, PhoneShop, Shop, normalize_name

from webapp.user.forms import SearchForm

blueprint = Blueprint('main', __name__)


@blueprint.route('/')
@blueprint.route('/index')
def index():
    form = SearchForm()
    title = 'Stuff Finder'
    text = request.args.get('search')
    nothing_found = True

    if text:
        all_phones = Phone.query.all()
        phones = []
        for phone in all_phones:
            ratio1 = fuzz.partial_ratio(normalize_name(phone.name), text)
            ratio2 = fuzz.token_set_ratio(normalize_name(phone.name), text)
            if ratio1 + ratio2 == 200:
                phones = [phone]
                break
            if ratio1 + ratio2 > 150:
                phones.append([phone, ratio1 + ratio2])
        if len(phones) > 1:
            phones = [i[0] for i in sorted(phones, key=lambda x: x[1], reverse=True)]
        if phones:
            nothing_found = False
        return render_template('main/index.html', page_title=title, phones=get_prices(phones), form=form,
                               nothing_found=nothing_found)

    nothing_found = False
    phones = Phone.query.all()
    return render_template('main/index.html', page_title=title, phones=get_prices(phones), form=form,
                           nothing_found=nothing_found)


def get_prices(phones):
    """ Функция формирует словарь {телефон: минимальная_цена} для последующего вывода в шаблоне"""

    out = {}
    for phone in phones:
        prices = [round(shop.price) for shop in phone.shops]
        out[phone] = min(prices) if prices else None
    return out


@blueprint.route('/specs')
def show_specs():
    phone_id = request.args.get('phone_id', None)
    phone = Phone.query.filter_by(id=phone_id).first()
    price_queries = PhoneShop.query.filter_by(phone_id=phone_id).all()
    prices = []
    for query in price_queries:
        shop = Shop.query.filter_by(id=query.shop_id).first()

        price = str(round(query.price))
        price = price[:len(price) - 3] + ' ' + price[-3:]
        shop_name = shop.name
        url = shop.phones_path + query.external_id
        prices.append([shop_name, price, url])
    if not prices:
        prices = [[], [], []]
    return render_template('main/specs.html', phone=phone, prices=prices)

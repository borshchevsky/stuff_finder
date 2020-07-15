from flask import Blueprint, render_template, request, url_for
from fuzzywuzzy import fuzz

from models import db, Phone, PhoneShop, Shop, normalize_name
from webapp.config import ITEMS_PER_PAGE

blueprint = Blueprint('main', __name__)


@blueprint.route('/')
@blueprint.route('/index')
def index():
    title = 'Stuff Finder'
    text = request.args.get('search')
    how = request.args.get('how')
    nothing_found = True

    if text:
        if how == 'pop':
            all_phones = Phone.query.order_by(Phone.views).all()
        else:
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
        return render_template('main/index.html', page_title=title, phones=get_prices(phones),
                               nothing_found=nothing_found)

    nothing_found = False
    page = request.args.get('page', 1, type=int)
    if how == 'pop':
        phones = Phone.query.order_by(Phone.views.desc()).paginate(page, ITEMS_PER_PAGE, False)
    elif how == 'price':
        phones = db.session.query(PhoneShop.phone_id, db.func.min(PhoneShop.price).label('min_price')) \
            .group_by(PhoneShop.phone_id, PhoneShop.price).order_by(PhoneShop.price.desc()) \
            .paginate(page, ITEMS_PER_PAGE, False)
    else:
        phones = Phone.query.paginate(page, ITEMS_PER_PAGE, False)
    next_url = url_for('main.index', page=phones.next_num) if phones.has_next else None
    prev_url = url_for('main.index', page=phones.prev_num) if phones.has_prev else None
    if how == 'price':
        phones_price_sorted = {}
        for item in phones.items:
            phones_price_sorted[Phone.query.filter_by(id=item.phone_id).first()] = round(item.min_price)
        phones = phones_price_sorted
    else:
        phones = get_prices(phones.items)

    return render_template('main/index.html', page_title=title, phones=phones,
                           nothing_found=nothing_found, next_url=next_url, prev_url=prev_url, how=how)


def get_prices(phones):
    """ Функция формирует словарь {телефон: минимальная_цена} для последующего вывода в шаблоне"""

    out = {}
    for phone in phones:
        prices = [round(shop.price) for shop in phone.shops if shop.price]
        out[phone] = str(min(prices)) if prices else None
    return out





@blueprint.route('/specs')
def show_specs():
    phone_id = request.args.get('phone_id', None)
    phone = Phone.query.filter_by(id=phone_id).first()
    if not phone:
        return render_template('errors/404.html')
    views = 1 if not phone.views else phone.views + 1
    Phone.query.filter_by(id=phone.id).update({'views': views})
    db.session.commit()
    price_queries = PhoneShop.query.filter_by(phone_id=phone_id).all()
    prices = []
    for query in price_queries:
        shop = Shop.query.filter_by(id=query.shop_id).first()
        if not query.price:
            continue
        price = str(round(query.price))
        price = price[:len(price) - 3] + ' ' + price[-3:]
        shop_name = shop.name
        url = shop.phones_path + query.external_id
        prices.append([shop_name, price, url])
    if not prices:
        prices = [[], [], []]
    return render_template('main/specs.html', phone=phone, prices=prices, page_title=phone.name)

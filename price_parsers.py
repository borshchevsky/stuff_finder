from collections import namedtuple
import json
import logging
import time
import sys

from bs4 import BeautifulSoup
import requests
from fuzzywuzzy import fuzz

from models import db, Phone, PhoneShop, Shop, normalize_name
from webapp import create_app


class CitilinkParser():
    URL = 'https://www.citilink.ru/catalog/mobile/smartfony/'
    SLEEP_TIME = 0.5
    SHOP_NAME = 'Ситилинк'
    END_PAGE = 28

    def parse_prices(self, start_page=1):
        page = start_page
        prices = []
        Price = namedtuple('Price', 'name price external_id', )
        print('Parsing...')
        while page <= self.END_PAGE:
            sys.stdout.write('\r')
            print(f'Page: {page}', end='')
            url = f'{self.URL}?p={page}'
            r = requests.get(url)
            parser = BeautifulSoup(r.text, 'html.parser')
            tags = parser.find_all('div', class_='subcategory-product-item')
            for item in tags:
                info = json.loads(item.find('div', class_='actions')['data-params'])
                name = info['shortName']
                if 'Как новый' in name:
                    continue
                price = info['price']
                external_id = info['id']
                prices.append(Price(name, price, external_id))
            time.sleep(self.SLEEP_TIME)
            page += 1
        print('\n')
        print(f'Done. {len(prices)} prices collected.')
        return prices

    def update_db(self):
        prices = self.parse_prices()
        total_prices = len(prices)
        n = 0
        phones = Phone.query.all()
        shop_id = Shop.query.filter_by(name=self.SHOP_NAME).first().id
        added = 0
        updated = 0
        print('\n')
        print('Updating DB...')
        for item in prices:
            n += 1
            percent_done = round(n / total_prices * 100, 2)
            sys.stdout.write('\r')
            print(f'Percent done: {percent_done} %', end='')
            fuzzed_phones = {}

            if PhoneShop.query.filter_by(external_id=item.external_id).count():
                p = PhoneShop.query.filter_by(external_id=item.external_id).first()
                if p.price != item.price:
                    PhoneShop.query.filter_by(id=p.id).update({'price': item.price})
                    updated += 1
            else:
                for phone in phones:
                    ratio1 = fuzz.partial_ratio(normalize_name(phone.name), normalize_name(item.name))
                    ratio2 = fuzz.token_set_ratio(normalize_name(phone.name), normalize_name(item.name))
                    if ratio1 + ratio2 > 120:
                        fuzzed_phones[phone] = ratio1 + ratio2
                if fuzzed_phones:
                    closest = max(fuzzed_phones, key=fuzzed_phones.get)
                    p = PhoneShop(phone_id=closest.id, shop_id=shop_id, price=item.price, external_id=item.external_id)
                    db.session.add(p)
                    added += 1
                else:
                    continue
            db.session.commit()
        print('\n')
        print(f'Done. Added {added} queries. Updated {updated} queries')


class EldoradoParser():
    URL = 'https://www.eldorado.ru/c/vse-smartfony/'
    SLEEP_TIME = 1
    SHOP_NAME = 'Ситилинк'
    END_PAGE = 17

    def parse_ids(self, start_page=1):
        page = start_page
        info = []
        collected = 0
        print('Parsing...')
        while page <= self.END_PAGE:
            sys.stdout.write('\r')
            print(f'Page: {page}', end='')
            url = f'{self.URL}?page={page}'
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers)
            parser = BeautifulSoup(r.text, 'html.parser')
            all_data = parser.find('script', id='__NEXT_DATA__')
            data = json.loads(all_data.contents[0])
            phones = data['props']['initialState']['products']['products']
            for value in phones.values():
                name = value['name']
                price = float(value['price'])
                external_id = value['code']
                info.append([name, price, external_id])
                collected += 1
            page += 1
            time.sleep(self.SLEEP_TIME)
        print('\n')
        print(f'Done. The information about {collected} phones collected.')
        return info

    def update_db(self):
        ids = self.parse_ids()
        number_of_ids = len(ids)
        n = 0
        phones = Phone.query.all()
        shop_id = Shop.query.filter_by(name=self.SHOP_NAME).first().id
        added = 0
        updated = 0
        print('\n')
        print('Updating DB...')
        percent_before = 0
        for info in ids:
            n += 1
            percent_done = round(n / number_of_ids * 100, 2)
            sys.stdout.write('\r')
            print(f'Percent done: {percent_done} %', end='')
            name, price, external_id = info
            name = normalize_name(name)
            fuzzed_phones = {}
            if PhoneShop.query.filter_by(external_id=external_id).count():
                p = PhoneShop.query.filter_by(external_id=external_id).first()
                if p.price != price:
                    PhoneShop.query.filter_by(id=p.id).update({'price': price})
                    updated += 1
            else:
                for phone in phones:
                    ratio1 = fuzz.partial_ratio(normalize_name(phone.name), name)
                    ratio2 = fuzz.token_set_ratio(normalize_name(phone.name), name)
                    if ratio1 + ratio2 > 120:
                        fuzzed_phones[phone] = ratio1 + ratio2
                if fuzzed_phones:
                    closest = max(fuzzed_phones, key=fuzzed_phones.get)
                    p = PhoneShop(phone_id=closest.id, shop_id=shop_id, price=price, external_id=external_id)
                    db.session.add(p)
                    added += 1
                else:
                    continue
            if percent_done - percent_before > 10:
                db.session.commit()
                percent_before = percent_done
            db.session.commit()
        print('\n')
        print(f'Done. Added {added} queries. Updated {updated} queries')


class MtsParser():
    URL = 'https://www.eldorado.ru/c/vse-smartfony/'
    SLEEP_TIME = 1
    SHOP_NAME = 'Ситилинк'
    END_PAGE = 17

    def parse_prices(self, start_page=1):
        page = start_page
        while page <= self.END_PAGE:
            sys.stdout.write('\r')
            print(f'Page: {page}', end='')
            url = f'{self.URL}?p={page}'
            r = requests.get(url)
            parser = BeautifulSoup(r.text, 'html.parser')
            tags = parser.find_all('div', class_='subcategory-product-item')
            for item in tags:
                info = json.loads(item.find('div', class_='actions')['data-params'])
                name = info['shortName']
                if 'Как новый' in name:
                    continue
                price = info['price']
                external_id = info['id']
                prices.append(Price(name, price, external_id))
            time.sleep(self.SLEEP_TIME)
            page += 1
        print('\n')
        print(f'Done. {len(prices)} prices collected.')
        return prices



if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # EldoradoParser().update_db()
        CitilinkParser().update_db()
        # print(CitilinkParser().parse_prices())

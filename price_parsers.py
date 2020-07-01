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
    SLEEP_TIME = 1
    SHOP_NAME = 'Citilink'
    END_PAGE = 30

    def parse_ids(self, start_page=1):
        page = start_page
        ids = []
        print('Parsing...')
        while page <= self.END_PAGE:
            url = f'{self.URL}?p={page}'
            r = requests.get(url)
            parser = BeautifulSoup(r.text, 'html.parser')

            tags = parser.find_all('div', class_='wrap-img')
            sys.stdout.write('\r')
            for i in tags:
                *_, identifier, _ = i.find('a')['href'].split('/')
                ids.append(identifier)
            print(f'Page: {page}', end='')
            page += 1
            time.sleep(self.SLEEP_TIME)
        print('\n')
        print(f'Done. {len(ids)} ids collected.')
        return ids

    def get_price(self, product_id):
        if not product_id:
            logging.error('ID is not specified.')
            return
        tries = 0
        max_tries = 9
        while True:
            r = requests.get(f'https://www.citilink.ru/catalog/mobile/cell_phones/{product_id}/')
            parser = BeautifulSoup(r.text, 'html.parser')
            loading = parser.find('title').text
            if 'Загрузка' in loading:
                tries += 1
                if tries > max_tries:
                    logging.error('Can\'t load the page.')
                    return
                time.sleep(1)
                continue
            tag = parser.find('script', type='application/ld+json')
            try:
                data = json.loads(tag.contents[0])
            except AttributeError:
                return None
            name = data['name']
            price = float(data['offers']['price'])
            return name, price

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
        for phone_id in ids:
            n += 1
            time.sleep(2)
            info = self.get_price(phone_id)
            percent_done = round(n / number_of_ids * 100, 2)
            sys.stdout.write('\r')
            print(f'Percent done: {percent_done} %', end='')
            if not info:
                continue
            try:
                name, price = info
            except TypeError:
                continue
            name = normalize_name(name)
            if price == 0 or 'подержанный' in name.lower():
                continue
            fuzzed_phones = {}
            if PhoneShop.query.filter_by(external_id=phone_id).count():
                p = PhoneShop.query.filter_by(external_id=phone_id).first()
                if p.price != price:
                    PhoneShop.query.filter_by(id=p.id).update({'price': price})
                    updated += 1
            else:
                for phone in phones:
                    ratio = fuzz.token_set_ratio(normalize_name(phone.name), name)
                    fuzzed_phones[phone] = ratio
                closest = max(fuzzed_phones, key=fuzzed_phones.get)
                if fuzzed_phones[closest] > 80:
                    p = PhoneShop(phone_id=closest.id, shop_id=shop_id, price=price, external_id=phone_id)
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
    SHOP_NAME = 'Eldorado'
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
                    ratio = fuzz.token_set_ratio(normalize_name(phone.name), name)
                    fuzzed_phones[phone] = ratio
                closest = max(fuzzed_phones, key=fuzzed_phones.get)
                if fuzzed_phones[closest] > 80:
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


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        EldoradoParser().update_db()
        # CitilinkParser().update_db()
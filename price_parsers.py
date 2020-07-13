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
    SLEEP_TIME = 10
    SHOP_NAME = 'Ситилинк'
    START_PAGE = 1
    END_PAGE = 28  # 28

    def parse_prices(self):
        page = self.START_PAGE
        prices = []
        Price = namedtuple('Price', 'name price external_id')
        print('Parsing Citilink...')
        headers = {'User-Agent': 'Mozilla/5.0'}
        while page <= self.END_PAGE:
            sys.stdout.write('\r')
            print(f'Page: {page}', end='')
            url = f'{self.URL}?p={page}'
            r = requests.get(url, headers=headers)
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

            if PhoneShop.query.filter_by(external_id=item.external_id, shop_id=shop_id).count():
                p = PhoneShop.query.filter_by(external_id=item.external_id).first()
                if p.price != item.price:
                    PhoneShop.query.filter_by(id=p.id).update({'price': item.price})
                    updated += 1
            else:
                for phone in phones:
                    ratio_w = fuzz.WRatio(normalize_name(phone.name), normalize_name(item.name))
                    if ratio_w > 86:
                        fuzzed_phones[phone] = ratio_w
                if fuzzed_phones:
                    closest = max(fuzzed_phones, key=fuzzed_phones.get)
                    if not PhoneShop.query.filter_by(phone_id=closest.id, shop_id=shop_id).count():
                        p = PhoneShop(phone_id=closest.id, shop_id=shop_id, price=item.price,
                                      external_id=item.external_id)
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
    SHOP_NAME = 'Эльдорадо'
    END_PAGE = 17  # 17

    def parse_ids(self, start_page=1):
        page = start_page
        info = []
        collected = 0
        print('Parsing Eldorado...')
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
            fuzzed_phones = {}
            if PhoneShop.query.filter_by(external_id=external_id, shop_id=shop_id).count():
                p = PhoneShop.query.filter_by(external_id=external_id).first()
                if p.price != price:
                    PhoneShop.query.filter_by(id=p.id).update({'price': price})
                    updated += 1
            else:
                for phone in phones:
                    ratio_w = fuzz.WRatio(normalize_name(phone.name), normalize_name(name))
                    if ratio_w > 86:
                        fuzzed_phones[phone] = ratio_w
                if fuzzed_phones:
                    closest = max(fuzzed_phones, key=fuzzed_phones.get)
                    if not PhoneShop.query.filter_by(phone_id=closest.id, shop_id=shop_id).count():
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
    URL = 'https://shop.mts.ru'
    SLEEP_TIME = 1
    SHOP_NAME = 'МТС'

    def parse_ids(self, start_page=1, end_page=25):
        page = start_page
        ids = []
        print('Parsing MTS...')
        while page <= end_page:
            sys.stdout.write('\r')
            print(f'Page: {page}', end='')

            url = f'{self.URL}/catalog/smartfony/{page}'
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers)
            parser = BeautifulSoup(r.text, 'html.parser')
            tags = parser.find_all('div', class_='image-right-wrapper')
            ids += [f'{item.find("a")["href"]}' for item in tags]
            page += 1
            time.sleep(self.SLEEP_TIME)

        print('\n')
        print(f'Done. {len(ids)} ids collected.\n')
        return ids

    def get_price(self, product_id):
        if not product_id:
            logging.error('ID is not specified.')
            return
        url = f'{self.URL}{product_id}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        parser = BeautifulSoup(r.content.decode('utf-8'), 'html.parser')
        name_tag = parser.find('meta', itemprop='name')
        try:
            prc = parser.find('meta', itemprop='price')['content']
        except TypeError:
            return
        Price = namedtuple('Price', 'name price external_id')
        return Price(name_tag['content'], prc, product_id)

    def parse_prices(self):
        ids = self.parse_ids()
        print('Parsing prices...')
        n = 1
        total = len(ids)
        prices = []
        for item in ids:
            sys.stdout.write('\r')
            print(f'Got price for {n} of {total} items.', end='')
            price = self.get_price(item)
            if not price:
                continue
            prices.append(price)
            n += 1
            time.sleep(self.SLEEP_TIME)
        print('\nDone.')
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

            if PhoneShop.query.filter_by(external_id=item.external_id, shop_id=shop_id).count():
                p = PhoneShop.query.filter_by(external_id=item.external_id).first()
                if p.price != item.price:
                    PhoneShop.query.filter_by(id=p.id).update({'price': item.price})
                    updated += 1
            else:
                for phone in phones:
                    ratio_w = fuzz.WRatio(normalize_name(phone.name), normalize_name(item.name))
                    if ratio_w > 86:
                        fuzzed_phones[phone] = ratio_w
                if fuzzed_phones:
                    closest = max(fuzzed_phones, key=fuzzed_phones.get)
                    if not PhoneShop.query.filter_by(phone_id=closest.id, shop_id=shop_id).count():
                        p = PhoneShop(phone_id=closest.id, shop_id=shop_id, price=item.price,
                                      external_id=item.external_id)
                        db.session.add(p)
                        added += 1
                else:
                    continue
            db.session.commit()
        print('\n')
        print(f'Done. Added {added} queries. Updated {updated} queries')


class TechportParser():
    URL = 'https://www.techport.ru/katalog/smartfony'
    SLEEP_TIME = 1
    SHOP_NAME = 'Техпорт'
    START_PAGE = 1
    END_PAGE = 7  # 28

    def parse_prices(self):
        page = self.START_PAGE
        offset = 0
        prices = []
        Price = namedtuple('Price', 'name price external_id')
        print('Parsing Techport...')
        headers = {'User-Agent': 'Mozilla/5.0'}
        while page <= self.END_PAGE:
            sys.stdout.write('\r')
            print(f'Page: {page}', end='')
            url = f'{self.URL}?offset={offset}'
            r = requests.get(url, headers=headers)
            parser = BeautifulSoup(r.text, 'html.parser')
            tags = parser.find_all('div', class_='tcp-product-media')
            for tag in tags:
                data = tag.find('a', class_='gtm-clk')
                name = data['data-gtm-name']
                price = data['data-gtm-price']
                external_id = data['href']
                prices.append(Price(name, price, external_id))
            time.sleep(self.SLEEP_TIME)
            page += 1
            offset += page * 28

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

            if PhoneShop.query.filter_by(external_id=item.external_id, shop_id=shop_id).count():
                p = PhoneShop.query.filter_by(external_id=item.external_id).first()
                if p.price != item.price:
                    PhoneShop.query.filter_by(id=p.id).update({'price': item.price})
                    updated += 1
            else:
                for phone in phones:
                    ratio_w = fuzz.WRatio(normalize_name(phone.name), normalize_name(item.name))
                    if ratio_w > 86:
                        fuzzed_phones[phone] = ratio_w
                if fuzzed_phones:
                    closest = max(fuzzed_phones, key=fuzzed_phones.get)
                    if not PhoneShop.query.filter_by(phone_id=closest.id, shop_id=shop_id).count():
                        p = PhoneShop(phone_id=closest.id, shop_id=shop_id, price=item.price,
                                      external_id=item.external_id)
                        db.session.add(p)
                        added += 1
                else:
                    continue
            db.session.commit()
        print('\n')
        print(f'Done. Added {added} queries. Updated {updated} queries')


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        TechportParser().update_db()
        # CitilinkParser().update_db()
        # EldoradoParser().update_db()
        # MtsParser().update_db()

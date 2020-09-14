import smtplib
from abc import abstractmethod
from collections import namedtuple
import json
import time
import sys


from bs4 import BeautifulSoup
from celery import Celery
import requests
from fuzzywuzzy import fuzz

from models import db, Phone, PhoneShop, Shop, User, user_phone, normalize_name
from webapp import create_app
from webapp.config import PROXIES


class BaseParser:
    SHOP_NAME = ''

    @abstractmethod
    def parse_prices(self):
        pass

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
                ps = PhoneShop.query.filter_by(external_id=item.external_id).first()
                if ps.price != item.price:
                    p = Phone.query.filter_by(id=ps.phone_id).first()
                    if item.price < get_min_price(p):
                        phone_shop_entries = db.session.query(user_phone).filter_by(phone_id=ps.phone_id).all()
                        emails = [User.query.filter_by(id=entry[0]).first().email for entry in phone_shop_entries]
                        if emails:
                            from tasks import send_mail
                            for email in emails:
                                send_mail.delay(email, p.name)
                    PhoneShop.query.filter_by(id=ps.id).update({'price': item.price})
                    updated += 1
            else:
                for phone in phones:
                    ratio_w = fuzz.WRatio(normalize_name(phone.name), normalize_name(item.name))
                    if ratio_w > 86:
                        fuzzed_phones[phone] = ratio_w
                if fuzzed_phones:
                    closest = max(fuzzed_phones, key=fuzzed_phones.get)
                    if not PhoneShop.query.filter_by(phone_id=closest.id, shop_id=shop_id).count():
                        ps = PhoneShop(phone_id=closest.id, shop_id=shop_id, price=item.price,
                                       external_id=item.external_id)
                        db.session.add(ps)
                        added += 1
                else:
                    continue
            db.session.commit()
        print('\n')
        print(f'Done. Added {added} queries. Updated {updated} queries')


class CitilinkParser():
    URL = 'https://www.citilink.ru/catalog/mobile/smartfony/'
    SLEEP_TIME = 2
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
            r = requests.get(url, headers=headers, proxies=PROXIES)
            parser = BeautifulSoup(r.text, 'html.parser')
            tags = parser.find_all('div', class_='subcategory-product-item')
            for item in tags:
                info = json.loads(item.find('div', class_='actions')['data-params'])
                name = info['shortName']
                if 'Как новый' in name:
                    continue
                price = float(info['price'])
                if not price:
                    continue
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
                if not price:
                    continue
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


class TechportParser(BaseParser):
    URL = 'https://www.techport.ru/katalog/smartfony'
    SLEEP_TIME = 1
    SHOP_NAME = 'Техпорт'
    START_PAGE = 1
    END_PAGE = 9  # 9

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
                if not price:
                    continue
                price = float(price)
                external_id = data['href']
                prices.append(Price(name, price, external_id))
            time.sleep(self.SLEEP_TIME)
            page += 1
            offset += page * 28

        print('\n')
        print(f'Done. {len(prices)} prices collected.')
        return prices


class MtsParser(BaseParser):
    URL = 'https://shop.mts.ru/catalog/smartfony/'
    SLEEP_TIME = 1
    SHOP_NAME = 'МТС'
    START_PAGE = 1
    END_PAGE = 25  # 25

    def parse_prices(self):
        page = self.START_PAGE
        prices = []
        Price = namedtuple('Price', 'name price external_id')
        print('Parsing MTS...')
        headers = {'User-Agent': 'Mozilla/5.0'}
        while page <= self.END_PAGE:
            sys.stdout.write('\r')
            print(f'Page: {page}', end='')
            url = f'{self.URL}?page={page}'
            r = requests.get(url, headers=headers)
            parser = BeautifulSoup(r.text, 'html.parser')
            tags = parser.find_all('div', class_='card-product__content')
            for tag in tags:
                price = float(''.join(i for i in tag.find('div', class_='hidden-price').text if i.isdigit()))
                if not price:
                    continue
                name_tag = tag.find('div', class_='card-product-description').find('a')
                name = name_tag['aria-label']
                external_id = name_tag['href']
                prices.append(Price(name, price, external_id))
            time.sleep(self.SLEEP_TIME)
            page += 1

        print('\n')
        print(f'Done. {len(prices)} prices collected.')
        return prices


class MegafonParser(BaseParser):
    URL = 'https://moscow.shop.megafon.ru/mobile'
    SLEEP_TIME = 1
    SHOP_NAME = 'Мегафон'
    START_PAGE = 1
    END_PAGE = 18  # 18

    def parse_prices(self):
        page = self.START_PAGE
        prices = []
        Price = namedtuple('Price', 'name price external_id')
        print('Parsing Megafon...')
        headers = {'User-Agent': 'Mozilla/5.0'}
        while page <= self.END_PAGE:
            sys.stdout.write('\r')
            print(f'Page: {page}', end='')
            url = f'{self.URL}?page={page}'
            r = requests.get(url, headers=headers)
            parser = BeautifulSoup(r.text, 'html.parser')
            tags = parser.find_all('div', class_='b-good__inside good')
            for tag in tags:
                name = tag.find('div', class_='b-good__title-entity')['title']
                price = tag.find('span', class_='b-price-good-list__value b-price__value').text.replace(' ', '')
                if not price:
                    continue
                price = float(price)
                external_id = tag.find('a')['href']
                prices.append(Price(name, price, external_id))
            time.sleep(self.SLEEP_TIME)
            page += 1

        print('\n')
        print(f'Done. {len(prices)} prices collected.')
        return prices


def get_min_price(phone):
    return min(shop.price for shop in phone.shops)

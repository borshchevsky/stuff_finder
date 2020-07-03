import logging
import os
import time
import sys
from bs4 import BeautifulSoup
import requests

from models import db, Phone, normalize_name
from parsers import BaseParser
from webapp import create_app

logging.basicConfig(
    filename='sf.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

'''Парсер для загрузки характеристик в карточку товара'''


class MtsParser(BaseParser):
    URL = 'https://shop.mts.ru'
    SLEEP_TIME = 1

    def parse_ids(self, start_page=1, end_page=25):
        page = start_page
        ids = []
        print('Parsing...')
        while page <= end_page:
            sys.stdout.write('\r')
            print(f'Page: {page}', end='')

            url = f'{self.URL}/catalog/smartfony/{page}'
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers)
            parser = BeautifulSoup(r.text, 'html.parser')
            tags = parser.find_all('div', class_='image-right-wrapper')
            ids += [f'{item.find("a")["href"]}/specs' for item in tags]
            page += 1
            time.sleep(self.SLEEP_TIME)

        print('\n')
        print(f'Done. {len(ids)} ids collected.\n')
        return ids

    def get_specs(self, product_id):
        if not product_id:
            logging.error('ID is not specified.')
            return
        url = f'{self.URL}{product_id}'
        r = requests.get(url)
        parser = BeautifulSoup(r.text, 'html.parser')
        name_tag = parser.find('meta', itemprop='name')
        all_data = parser.find_all('table', class_='detail-good__attributs')
        images_table = parser.find('div', class_='thumbs tablet-only')
        images_tags = images_table.find_all('a')
        img_list = []
        for i in range(3):
            try:
                img = images_tags[i]['data-large-image']
                end = img.index('jpg') + 3
                img = img[0:end]
                img_list.append(img)
            except(IndexError, ValueError):
                break
        img_string = ','.join(iter(img_list))
        data = {}
        data['name'] = name_tag['content']
        data['url'] = url
        data['images'] = img_string
        for item in all_data:
            names = item.find_all('td', class_='name')
            values = item.find_all('td', class_='value')
            for n, name in enumerate(names):
                data[name.text] = values[n].text
        return data

    def process_data(self, data):
        if not data:
            logging.error('No data to process.')
            return
        phone = Phone()
        phone.name = data['name']
        phone.photos = data.get('images')
        phone.os = data.get('Операционная система')
        try:
            phone.num_of_sims = int(data['Количество SIM-карт'])
        except KeyError:
            phone.num_of_sims = None
        phone.sim_type = data.get('Тип SIM-карты')
        try:
            phone.weight = float(''.join(i for i in data['Вес'] if i.isdigit() or i == '.'))
        except KeyError:
            phone.weight = None
        try:
            height = data['Высота'].split()[0]
            width = data['Ширина'].split()[0]
            depth = data['Толщина'].split()[0]
            phone.size = f'{height},{width},{depth}'
        except KeyError:
            phone.size = None
        try:
            phone.screen_size = float(data['Диагональ экрана'].split()[0])
        except KeyError:
            phone.screen_size = None
        phone.screen_type = data.get('Тип цветного экрана')
        phone.resolution = data.get('Разрешение экрана')
        try:
            phone.ppi = int(''.join(i for i in data['Плотность точек'] if i.isdigit()))
        except KeyError:
            phone.ppi = 0
        phone.main_cam_resolution = data.get('Разрешение основной камеры')
        phone.aperture = data.get('Диафрагма основной камеры')
        phone.selfie_aperture = data.get('Диафрагма фронтальной камеры')
        phone.selfie_cam_resolution = data.get('Разрешение фронтальной камеры')
        phone.max_video_resolution = data.get('Разрешение видеосъемки основной камеры (макс)')
        phone.headphones_jack = data.get('Разъем для наушников')
        phone.processor = data.get('Процессор')
        try:
            phone.sdcard_slot = data.get('Слот для карты памяти').lower()
        except AttributeError:
            phone.sdcard_slot = None
        return phone

    def parse_all(self):
        mts = MtsParser()
        ids = mts.parse_ids(1, 25)
        items_added = 0
        for n, i in enumerate(ids):
            data = mts.get_specs(i)
            item = mts.process_data(data)
            if mts.save_to_db(item):
                items_added += 1
            sys.stdout.write('\r')
            percent_done = round((n / len(ids)) * 100, 2)
            print(f'Saving data... {percent_done} % done', end='')
        print('\n')
        print(f'Done. {items_added} new items added.\n')

    def save_to_db(self, data):
        item_exists = Phone.query.filter(Phone.name == data.name).count()
        if not item_exists:
            db.session.add(data)
            db.session.commit()
            return True

    def download_images(self):
        counter = 0
        dirpath = os.path.join('webapp', 'static')
        os.makedirs(dirpath, exist_ok=True)
        for item in Phone.query.order_by(Phone.name.desc()).all():
            if item.photos:
                for n, photo in enumerate(item.photos.split(','), start=1):
                    if not photo.endswith('jpg'):
                        continue
                    name = item.name.replace("/", "").strip()
                    filename = f'{name} {n}.jpg'
                    fullpath = os.path.join(dirpath, filename)
                    if os.path.isfile(fullpath):
                        continue
                    url = self.URL + photo
                    photo_to_download = requests.get(url).content
                    with open(fullpath, 'wb') as handler:
                        handler.write(photo_to_download)
                    counter += 1
                    sys.stdout.write('\r')
                    print(f'Photos downloaded: {counter}', end='')
        print('\n')
        print(f'Done. Photos downloaded: {counter}')


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # MtsParser().parse_all()
        MtsParser().download_images()
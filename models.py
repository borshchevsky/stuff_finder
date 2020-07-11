import logging

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

logging.basicConfig(
    filename='sf.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class Phone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True, unique=True)
    views = db.Column(db.Integer)

    # Общие характеристики
    photos = db.Column(db.String, nullable=True)
    os = db.Column(db.String, nullable=True)
    num_of_sims = db.Column(db.String, nullable=True)
    sim_type = db.Column(db.String, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    size = db.Column(db.String,
                     nullable=True)  # наверное лучше указать размер строкой вида "160, 80, 20", а потом её сплитить
    # url = db.Column(db.String, nullable=True, unique=True)

    # Экран
    screen_type = db.Column(db.String, nullable=True)
    screen_size = db.Column(db.String, nullable=True)
    resolution = db.Column(db.String, nullable=True)
    ppi = db.Column(db.String, nullable=True)
    ips = db.Column(db.String, nullable=True)

    # Мультимедиа
    main_cam_resolution = db.Column(db.String, nullable=True)
    selfie_cam_resolution = db.Column(db.String, nullable=True)
    aperture = db.Column(db.String, nullable=True)
    selfie_aperture = db.Column(db.String, nullable=True)
    flash = db.Column(db.String, nullable=True)
    max_video_resolution = db.Column(db.String, nullable=True)
    selfie_cam = db.Column(db.String, nullable=True)
    audio_formats = db.Column(db.String, nullable=True)
    headphones_jack = db.Column(db.String, nullable=True)

    # Связь
    types = db.Column(db.String, nullable=True)
    bluetooth_version = db.Column(db.String, nullable=True)

    # Батарея
    battery_capacity = db.Column(db.String, nullable=True)
    charge_connector = db.Column(db.String, nullable=True)
    quick_charge = db.Column(db.String, nullable=True)

    # Память и процессор
    processor = db.Column(db.String, nullable=True)
    processor_cores = db.Column(db.String, nullable=True)
    gpu = db.Column(db.String, nullable=True)
    ram = db.Column(db.String, nullable=True)
    sdcard_slot = db.Column(db.String, nullable=True)

    shops = db.relationship('PhoneShop')

    def __repr__(self):
        return f'<Phone class {self.name}>'


class PhoneShop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_id = db.Column(db.Integer, db.ForeignKey('phone.id'))
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    price = db.Column(db.Float)
    test = db.Column(db.String)
    external_id = db.Column(db.String)


user_phone = db.Table(
    'user_phone',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('phone_id', db.Integer, db.ForeignKey('phone.id'), primary_key=True)
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120))
    name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    password = db.Column(db.String)
    favorites = db.relationship('Phone', secondary=user_phone)

    def __repr__(self):
        return f'<User class {self.name}>'

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password):
        self.password = generate_password_hash(password)


class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    url = db.Column(db.String, unique=True)
    phones_path = db.Column(db.String)

    def __repr__(self):
        return f'<Shop class {self.name}>'

    def add(self, name, url, phones_path):
        exists = Shop.query.filter_by(url=url).count()
        if exists:
            print('Shop already exists.')
            return
        shop = Shop(name=name, url=url, phones_path=phones_path)
        db.session.add(shop)
        db.session.commit()
        print('New shop added.')


def normalize_name(name):
    bad_words = {'смартфон', 'мобильный', 'телефон'}
    replace_dict = {
        'красный': 'red',
        'синий': 'blue',
        'черный': 'black',
        'серый': 'grey',
        'зеленый': 'green',
        'зелёный': 'green',
        'коричневый': 'brown',
        'золотистый': 'gold',
        'золотой': 'gold',
    }
    words = name.split()
    result = ' '.join(word for word in words if word.lower() not in bad_words)
    for replace_what, replace_to in replace_dict.items():
        result = result.replace(replace_what, replace_to)
    if 'gb' in result.lower() and result.find(' gb') == -1:
        index = result.lower().find('gb')
        result = result[:index] + ' ' + result[index:]
    return result


if __name__ == '__main__':
    print(generate_password_hash('asd'))

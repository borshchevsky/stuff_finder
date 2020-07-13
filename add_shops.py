from models import Shop
from webapp import create_app


app = create_app()
with app.app_context():
    Shop().add('Ситилинк', 'www.citilink.ru', 'https://www.citilink.ru/catalog/mobile/cell_phones/')
    Shop().add('МТС', 'http://shop.mts.ru', 'https://shop.mts.ru/product/')
    Shop().add('Эльдорадо', 'www.eldorado.ru', 'https://www.eldorado.ru/cat/detail/')
    Shop().add('Техпорт', 'www.techport.ru', 'https://www.techport.ru')

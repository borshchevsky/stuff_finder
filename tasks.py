from celery import Celery
from celery.schedules import crontab

from webapp import create_app
import price_parsers

flask_app = create_app()
celery_app = Celery('tasks', broker='redis://localhost:6379/0')


@celery_app.on_after_configure.connect
def setup_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour='*/5'), update_prices_megafon.s())
    sender.add_periodic_task(crontab(hour='*/5'), update_prices_eldorado.s())
    sender.add_periodic_task(crontab(hour='*/5'), update_prices_techport.s())
    # sender.add_periodic_task(crontab(hour='*/5'), update_prices_citilink.s())
    sender.add_periodic_task(crontab(hour='*/5'), update_prices_mts.s())


@celery_app.task
def update_prices_megafon():
    with flask_app.app_context():
        price_parsers.MegafonParser().update_db()


@celery_app.task
def update_prices_eldorado():
    with flask_app.app_context():
        price_parsers.EldoradoParser().update_db()


@celery_app.task
def update_prices_techport():
    with flask_app.app_context():
        price_parsers.TechportParser().update_db()


@celery_app.task
def update_prices_citilink():
    with flask_app.app_context():
        price_parsers.CitilinkParser().update_db()


@celery_app.task
def update_prices_mts():
    with flask_app.app_context():
        price_parsers.MtsParser().update_db()



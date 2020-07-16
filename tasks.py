import smtplib
from email.header import Header
from email.mime.text import MIMEText

from celery import Celery
from celery.schedules import crontab

from webapp import create_app
import price_parsers
from webapp.config import MAIL_SERVER, MAIL_LOGIN, MAIL_PASSWORD

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
        import price_parsers
        price_parsers.MegafonParser().update_db()


@celery_app.task
def update_prices_eldorado():
    with flask_app.app_context():
        import price_parsers
        price_parsers.EldoradoParser().update_db()


@celery_app.task
def update_prices_techport():
    with flask_app.app_context():
        import price_parsers
        price_parsers.TechportParser().update_db()


@celery_app.task
def update_prices_citilink():
    with flask_app.app_context():
        import price_parsers
        price_parsers.CitilinkParser().update_db()


@celery_app.task
def update_prices_mts():
    with flask_app.app_context():
        import price_parsers
        price_parsers.MtsParser().update_db()


@celery_app.task
def send_mail(email):
    to = email
    body = f'asd'

    msg = MIMEText(body.encode('utf-8'), 'plain', 'utf-8')
    msg['Subject'] = Header('price sadad', 'utf-8')
    msg['From'] = 'admin@rattle.one'
    msg['To'] = email

    server = smtplib.SMTP(MAIL_SERVER)
    server.starttls()
    server.login(MAIL_LOGIN, MAIL_PASSWORD)
    server.sendmail(msg['From'], [to], msg.as_string())
    server.quit()

if __name__ == '__main__':
    send_mail('3410914@gmail.com')